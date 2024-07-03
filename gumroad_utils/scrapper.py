import json
import logging
import re
import sys
from collections import defaultdict
from datetime import date

import humanize
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
from pathlib3x import Path
from requests import Session as _RequestsSession
from rich.progress import Progress as RichProgress

__all__ = ["GumroadScrapper", "GumroadSession"]

_ARCHIVES_EXT = {"rar", "zip"}


def _load_json_data(soup: BeautifulSoup, data_component_name: str) -> dict:
    script = soup.find(
        "script",
        attrs={
            "class": "js-react-on-rails-component",
            "data-component-name": data_component_name,
        },
    )
    return json.loads(script.string)


def _sanitize_cookie_value(value: str) -> str:
    return value.replace("+", "%2B").replace("/", "%2F").replace("=", "%3D")


# https://www.xormedia.com/string-truncate-middle-with-ellipsis/
def shorten(s: str, n: int = 40) -> str:
    if len(s) <= n:
        return s

    n_2 = int(n) / 2 - 3
    n_1 = n - n_2 - 3

    return "{0}..{1}".format(s[:int(n_1)], s[-int(n_2):])


class GumroadSession(_RequestsSession):
    def __init__(self, app_session: str, guid: str, user_agent: str) -> None:
        super().__init__()

        self.cookies.set("_gumroad_app_session", _sanitize_cookie_value(app_session))
        self.cookies.set("_gumroad_guid", guid)
        self.headers["User-Agent"] = user_agent

    @property
    def base_url(self) -> str:
        return "https://app.gumroad.com"

    def get_soup(self, url: str) -> BeautifulSoup:
        response = self.get(url, allow_redirects=False)
        response.raise_for_status()
        return BeautifulSoup(response.content, "lxml")


class FilesCache:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._storage: dict[str, set] = defaultdict(set)
        self._logger = logging.getLogger("cache")
        self.load()  # Load cache on initialization

    def load(self) -> None:
        if not self._file_path.exists():
            return

        with open(self._file_path, "r", encoding="utf-8") as f:
            for k, v in json.load(f).items():
                self._storage[k] = set(v)

        self._logger.info("Cache has been loaded.")

    def save(self) -> None:
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(self._storage, f, default=list, indent=2)

        self._logger.info("Cache has been saved.")

    def is_cached(self, product_id: str, file_id: str) -> bool:
        return file_id in self._storage.get(product_id, []) 

    def cache(self, product_id: str, file_id: str) -> None:
        self._storage[product_id].add(file_id)


class GumroadScrapper:
    def __init__(
        self,
        session: GumroadSession,
        files_cache: FilesCache,
        root_folder: Path,
        product_folder_tmpl: str,
        slash_replacement: str
    ) -> None:
        self._session = session
        self._root_folder = root_folder
        self._product_folder_tmpl = product_folder_tmpl
        self._slash_replacement = slash_replacement

        self._files_cache = files_cache
        self._logger = logging.getLogger("scraper")

    # Pages - Library

    def scrape_library(self, creators: set[str] = ".") -> None:
        soup = self._session.get_soup(self._session.base_url + "/library")
        self._detect_redirect(soup)

        script = _load_json_data(soup, "LibraryPage")

        for result in script["results"]:
            # NOTE(PxINKY) Seems on very very rare occasions the profile can be missing the 'creator' object 
            # Gumroad has dissallowed the username "none" from being picked, so it makes a good choice here
            creator_profile_url = "none"
            try:
                creator_profile_url = result["product"]["creator"]["profile_url"]
            except:
                self._logger.warning(
                    "Could not find creator for %r", result["product"]["name"]
                    )
                
            
            creator_username = "none" 
            # Gumroad added "?recommended_by=library" to the end of 'profile_url'
            try:
                creator_username = re.search(
                    r"https:\/\/(.*)\.gumroad\.com\?recommended_by=library", creator_profile_url
                ).group(1)
            except:
                self._logger.warning(
                    "Could not find creator in profile_url"
                    )
            
            # NOTE(PxINKY): Swapping to ID as a static variable, we can use a try-catch to reassign it if the creator's name does exist!
            creator = result["product"]["creator_id"]
            try:
                creator = result["product"]["creator"]["name"]
            except:
                self._logger.warning(
                    "Defaulting to creator ID (%r), creators name is missing", creator
                    )
            product = result["product"]["name"]
            # Since creators needs a default value, we make sure it is either changed or not.
            if creator_username not in creators and creators != ".":
                self._logger.debug("Skipping %r product of %r.", product, creator)
                continue

            if result["purchase"]["is_bundle_purchase"]:
                self._logger.info(
                    "Skipping %r product of %r because it's a bundle!", product, creator
                )
                continue

            updated_at = parse_date(result["product"]["updated_at"]).date()
            self.scrap_product_page(result["purchase"]["download_url"], updated_at) 

    
    # Pages - Product content

    def scrap_product_page(self, url: str, uploaded_at: date | None = None) -> None:
        if url.isalnum():
            url = f"{self._session.base_url}/d/{url}"

        self._logger.info("Scrapping %r...", url)

        soup = self._session.get_soup(url)
        self._detect_redirect(soup)

        script = _load_json_data(soup, "DownloadPageWithContent")

        # NOTE(PxINKY) Gumroad filters the username (Page URL / Profile Link username) on creation/edit
        # but not the "name" (["creator"]["name"]) from having invalid characters
        # additionally filenames can also contain invalid characters
        # Simply sanitizing the filename before using it fixes this issue
        product_creator = self.sanitize_filename(script["creator"]["name"].strip())
        product_name = self.sanitize_filename(script["purchase"]["product_name"])

        recipe_link = f"{self._session.base_url}/purchases/{script['purchase']['id']}/receipt"
        price = self._scrap_recipe_page(recipe_link)
        purchase_date = parse_date(script["purchase"]["created_at"]).date()

        try:
            product_folder_name = self._product_folder_tmpl.format(
                product_name=product_name,
                purchase_at=purchase_date,
                uploaded_at=uploaded_at,
                price=price,
            ).strip()
        except TypeError:
            self._logger.info("'uploaded_at' is not available!")
            sys.exit()

        product_folder: "Path" = self._root_folder / product_creator / product_folder_name

        # NOTE(obsessedcake): We might be able to download everything in a single zip archive.
        #   Download all -> Download as ZIP
        for action in soup.select(".actions button"):
            if "ZIP" not in action.find(text=True):
                continue

            # NOTE(obsessedcake): Creators can publish an single archive as a content for the product.
            #   If it's a case, let's download in a normal way.
            if self._content_is_archive(soup):
                break

            self._logger.info(
                "Downloading %r product of %r creator as a zip archive.",
                product_name,
                product_creator,
            )

            zip_url = url.replace("/d/", "/zip/")
            output = product_folder.append_suffix(".zip")

            self._fancy_download_file(zip_url, Path("/"), output, transient=False)
            return

        self._logger.info("Downloading %r product of %r creator...", product_name, product_creator)
        self._download_content(script, product_folder)

    def _content_is_archive(self, product_page_soup: BeautifulSoup) -> bool:
        tree_elements = product_page_soup.select(".js-file-list-element")
        if len(tree_elements) > 1:
            return False

        file_type = tree_elements[0].select_one("li:nth-child(1)").string.strip().lower()
        return file_type in _ARCHIVES_EXT

    
    # Item - scanner / Downloader  
    
    def _download_content(self, script: dict, parent_folder: Path) -> None:
        product_id = script["purchase"]["product_id"]

        def _traverse_tree(items: list[dict], tree_path: Path, parent_folder: Path) -> None:
            files_count = 0
            file_idx = 0

            for item in items:
                if item["type"] != "folder":
                    files_count += 1
                    continue

                folder_name = item["name"]
                _traverse_tree(
                    item["children"],
                    tree_path / folder_name.strip(),
                    parent_folder / folder_name.strip(),
                )

            for item in items:
                # NOTE(PxINKY) Gumroad added a "file" type that's embedded into the page resulting in no download_url
                if item["type"] != "file" or item["download_url"] is None:
                    continue

                file_id = item["id"]
                # Sanitize the file name
                # Issue arises if the file_name is something like: 'File 1.0 / 2.0'
                # Sanitizing the file_name should prevent this
                file_name = self.sanitize_filename(item["file_name"]) 
                file_type = item["extension"].lower()
                file_url = self._session.base_url + item["download_url"]

                file_path = (parent_folder / file_name).with_suffix("." + file_type)
                file_idx += 1

                self._fancy_download_file(
                    product_id,
                    file_id,
                    file_url,
                    tree_path,
                    file_path,
                    files_count,
                    file_idx,
                    transient=True,
                )

        _traverse_tree(script["content"]["content_items"], Path("/"), parent_folder)


    # Pages - Recipe
   
    def _scrap_recipe_page(self, url: str) -> str:
        soup = self._session.get_soup(url)
        payment_info_element = soup.select_one(".main > div:nth-child(1) > div")
        if payment_info_element:
            payment_info = payment_info_element.string
            if payment_info:
                price = payment_info.strip().split("\n")[0]  # \n$9.99\n— VISA *0000
                return price
        # NOTE(PxINKY) If the purchase is a gift, A recite cant be generated, return empty
        self._logger.warning("Failed to extract payment info from %s", url)
        return ""

    
    # (PxINKY) - File name sanitizer
    
    def sanitize_filename(self, filename: str) -> str:
        invalid_chars = r'<>:"/\|?*'
        # Replace invalid characters and spaces with underscores
        sanitized_filename = ''.join(self._slash_replacement if c in invalid_chars else c for c in filename)
        return sanitized_filename

    
    # File downloader
    
    def _fancy_download_file(
        self,
        product_id: str,
        file_id: str,
        url: str,
        tree_path: Path,
        file_path: Path,
        files_total_count: int = 0,
        file_idx: int = 0,
        *,
        transient: bool,
    ) -> None:
        tree_file_path = tree_path / file_path.name
        if self._files_cache.is_cached(product_id, file_id):
            self._logger.debug("'%s' is already downloaded! Skipping.", tree_file_path)
            return

        response = self._session.get(url, stream=True)
        response.raise_for_status()

        total_size_in_bytes = int(response.headers.get("content-length", 0))
        if total_size_in_bytes == 0:
            self._logger.warning(
                "Failed to download '%s' file, received zero content length!", tree_file_path
            )
            return

        human_size = humanize.naturalsize(total_size_in_bytes)
        if transient:
            task_desc = f"[{file_idx}/{files_total_count}] Downloading '{shorten(file_path.name)}' ({human_size})..."
        else:
            task_desc = "Downloading {human_size} file..."

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with RichProgress(expand=True, transient=transient) as progress:
            task = progress.add_task(task_desc, total=total_size_in_bytes)

            with file_path.open("wb") as file:
                for chunk in response.iter_content(chunk_size=4096):  # 4kb
                    if chunk:  # filter out keep-alive new chunks
                        progress.advance(task, len(chunk))
                        file.write(chunk)

        self._files_cache.cache(product_id, file_id)
        self._files_cache.save() # save after each sucsessful download
        self._logger.info("Downloaded '%s' to '%s'", tree_file_path, file_path)


    # Utils

    def _detect_redirect(self, soup: BeautifulSoup) -> None:
        text = soup.find(text=True, recursive=False)
        if text and ("You are being" in text):  # You are being redirected.
            raise RuntimeError("You are being redirected to a login page!")
