import gc
import logging
import signal
import sys
from configparser import RawConfigParser
from typing import cast

from pathlib3x import Path
from rich.logging import RichHandler

from .cli import get_cli_arg_parser
from .scrapper import FilesCache, GumroadScrapper, GumroadSession


def _set_sigint_handler(files_cache: FilesCache) -> None:
    original_sigint_handler = signal.getsignal(signal.SIGINT)

    def _sigint_handler(signal, frame):
        files_cache.save()
        original_sigint_handler(signal, frame)

    signal.signal(signal.SIGINT, _sigint_handler)


def main() -> None:
    try:
        args = get_cli_arg_parser().parse_args()
    except FileNotFoundError as e:
        print(f"File not found: {str(e)}!")
        sys.exit(1)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="[%(name)s] %(message)s",
        datefmt="%X",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    config = RawConfigParser()
    config.read(args.config)

    session = GumroadSession(
        app_session=config["user"]["app_session"],
        guid=config["user"]["guid"],
        user_agent=config["user"]["user_agent"],
    )
    files_cache = FilesCache(cast("Path", args.config).parent / "gumroad.cache")
    scrapper = GumroadScrapper(
        session,
        root_folder=args.output,
        product_folder_tmpl=config["scrapper"]["product_folder_tmpl"],
        slash_replacement=config["scrapper"]["slash_replacement"],
    )

    try:
        if isinstance(args.link, str) and (args.link == "library"):
            links = []
        elif isinstance(args.link, list):
            links = args.link
        elif args.links:
            links = cast(Path, args.links).open().readlines()
            if not links:
                logging.getLogger().debug("File with links is empty.")
                return

        if isinstance(args.creator, str):
            creators = {args.creator}
        elif isinstance(args.creator, list):
            creators = set(args.creator)
        else:
            creators = {}

        files_cache.load()
        _set_sigint_handler(files_cache)

        if links:
            for link in links:
                scrapper.scrap_product_page(link)
                gc.collect()
        else:
            scrapper.scrape_library(creators)

    except Exception:
        logging.getLogger().exception("")

    files_cache.save()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
