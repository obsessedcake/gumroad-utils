from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from typing import TYPE_CHECKING

from pathlib3x import Path

if TYPE_CHECKING:
    from argparse import _SubParsersAction

__all__ = ["get_cli_arg_parser"]


def _is_valid_path(file_path: str) -> Path:
    path = Path(file_path)
    if path.exists():
        return path
    else:
        raise FileNotFoundError(file_path)


def _to_path(file_path: str) -> Path:
    return Path(file_path)


def _add_parser(
    subparsers: "_SubParsersAction[ArgumentParser]",
    name: str,
    help: str,
) -> ArgumentParser:
    parser = subparsers.add_parser(
        name, help=help, description=help, formatter_class=ArgumentDefaultsHelpFormatter
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
    return parser


def get_cli_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="A set of useful utils for downloadingand wiping your gumroad.com library.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    # download

    dl = _add_parser(subparsers, "dl", "Download products")

    dl_links = dl.add_mutually_exclusive_group()
    dl_links.add_argument(
        "link",
        nargs="*",
        default="library",
        help="A product link or a list of them.",
    )
    dl_links.add_argument(
        "-k",
        "--creator",
        nargs="*",
        help="Download only products made by specified creators.",
        default=None,
    )
    dl_links.add_argument(
        "-l",
        "--links",
        type=_is_valid_path,
        help="A file with a list of products links.",
    )

    dl.add_argument(
        "-o",
        "--output",
        type=_to_path,
        help="An output directory (default: current directory).",
        default=Path.cwd(),
    )

    # wipe

    wipe = _add_parser(subparsers, "wipe", "Wipe products in your library")
    wipe.add_argument(
        "-k",
        "--creator",
        nargs="*",
        help="Wipe only products made by specified creators.",
        default=None,
    )

    return parser
