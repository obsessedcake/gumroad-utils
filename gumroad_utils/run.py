import gc
import logging
import signal
import sys
from configparser import RawConfigParser
from typing import cast

from pathlib3x import Path
from rich.logging import RichHandler

from .cli import get_cli_arg_parser
from .scrapper import GumroadScrapper, GumroadSession


def _set_sigint_handler(scrapper: GumroadScrapper, cache_file: Path) -> None:
    original_sigint_handler = signal.getsignal(signal.SIGINT)

    def _sigint_handler(signal, frame):
        scrapper.save_cache(cache_file)
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

        cache_file = cast("Path", args.config).parent / "gumroad.cache"
        scrapper.load_cache(cache_file)

        _set_sigint_handler(scrapper, cache_file)

        if links:
            for link in links:
                scrapper.scrap_product_page(link)
                gc.collect()
        else:
            scrapper.scrape_library(creators)

    except Exception:
        logging.getLogger().exception("")

    scrapper.save_cache(cache_file)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
