from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from pathlib3x import Path

__all__ = ["get_cli_arg_parser"]


def _is_valid_path(file_path: str) -> Path:
    path = Path(file_path)
    if path.exists():
        return path
    else:
        raise FileNotFoundError(file_path)


def _to_path(file_path: str) -> Path:
    return Path(file_path)


def get_cli_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="A simple downloader for gumroad.com products",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    links = parser.add_mutually_exclusive_group()
    parser.add_argument(
        "link",
        nargs="*",
        default="library",
        help="A product link or a list of them.",
    )
    links.add_argument(
        "-k",
        "--creator",
        nargs="*",
        help="Download only products made by specified creators.",
        default=None,
    )
    links.add_argument(
        "-l",
        "--links",
        type=_is_valid_path,
        help="A file with a list of products links.",
    )

    parser.add_argument(
        "--debug",
        help="Enable debug mode.",
        action="store_true",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=_is_valid_path,
        help="A path to configuration INI file.",
        default="config.ini",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=_to_path,
        help="An output directory (default: current directory).",
        default=Path.cwd(),
    )
    parser.add_argument(
        "-a",
        "--dl-all",
        action="store_true",
        help="Download all creators (default: false)"
    )

    return parser
