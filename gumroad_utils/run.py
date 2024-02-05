import gc
import logging
import signal
import sys
from argparse import ArgumentParser
from configparser import RawConfigParser
from typing import Any, cast

from pathlib3x import Path
from rich.logging import RichHandler

from .cli import get_cli_arg_parser
from .scrapper import GumroadDownloader, GumroadSession, GumroadWiper


def _get_creators(args: Any) -> set[str]:
    if isinstance(args.creator, str):
        return {args.creator}
    elif isinstance(args.creator, list):
        return set(args.creator)
    else:
        return {}


def _execute_download(args: Any, config: RawConfigParser, session: GumroadSession) -> None:
    if isinstance(args.link, str) and (args.link == "library"):
        links = []
    elif isinstance(args.link, list):
        links = args.link
    elif args.links:
        links = cast(Path, args.links).open().readlines()
        if not links:
            logging.getLogger().debug("File with links is empty.")
            return

    dl = GumroadDownloader(
        session,
        root_folder=args.output,
        product_folder_tmpl=config["scrapper"]["product_folder_tmpl"],
    )

    cache_file = cast("Path", args.config).parent / "gumroad.cache"
    dl.load_cache(cache_file)

    # Set SIGINT handler

    original_sigint_handler = signal.getsignal(signal.SIGINT)

    def _sigint_handler(signal, frame):
        dl.save_cache(cache_file)
        original_sigint_handler(signal, frame)

    signal.signal(signal.SIGINT, _sigint_handler)

    # Download

    if links:
        for link in links:
            dl.scrap_product_page(link)
            gc.collect()
    else:
        dl.scrape_library(_get_creators(args))

    dl.save_cache(cache_file)


def _execute_wipe(args: Any, config: RawConfigParser, session: GumroadSession) -> None:
    GumroadWiper(session).wipe(_get_creators(args))


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

    try:
        {"dl": _execute_download, "wipe": _execute_wipe}[args.command](args, config, session)
    except Exception:
        logging.getLogger().exception("")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
