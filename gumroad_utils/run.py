import gc
import logging
import sys
from configparser import RawConfigParser
from typing import TYPE_CHECKING, cast

from rich.logging import RichHandler

from .cli import get_cli_arg_parser
from .scrapper import GumroadScrapper, GumroadSession

if TYPE_CHECKING:
    from pathlib3x import Path


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
    scrapper = GumroadScrapper(
        session,
        root_folder=args.output,
        product_folder_tmpl=config["scrapper"]["product_folder_tmpl"],
    )

    try:
        if isinstance(args.link, str) and (args.link == "library"):
            links = []
        elif isinstance(args.link, list):
            links = args.link
        elif args.links:
            links = cast("Path", args.links).open().readlines()
            if not links:
                logging.getLogger().debug("File with links is empty.")
                return

        cache_file = cast("Path", args.config).parent / "gumroad.cache"
        scrapper.load_cache(cache_file)

        if links:
            for link in links:
                scrapper.scrap_product_page(link)
                gc.collect()
        else:
            scrapper.scrape_library()

        scrapper.save_cache(cache_file)
    except Exception:
        logging.getLogger().exception("")


if __name__ == "__main__":
    main()
