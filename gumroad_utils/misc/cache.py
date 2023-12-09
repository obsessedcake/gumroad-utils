import json
from enum import IntEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib3x import Path

__all__ = ["Cache", "DownloadStatus"]


class DownloadStatus(IntEnum):
    IN_PROGRESS = 0
    FINISHED = 1


class Cache:
    def __init__(self) -> None:
        self._files_cache: dict[str, set] = {}
        self._recipes_cache: dict[str, dict[str, Any]] = {}
        self._status: dict[str, DownloadStatus] = {}

    # I/O

    def load_cache(self, file_path: "Path") -> None:
        if not file_path.exists():
            return

        with open(file_path, "r", encoding="utf-8") as f:
            for k, v in json.load(f).items():
                self._files_cache[k] = set(v)

    def save_cache(self, file_path: "Path") -> None:
        data = {
            "files": self._files_cache,
            "recipes": self._recipes_cache,
            "status": self._status,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, default=list, indent=2)

    # Files

    def is_file_cached(self, product_id: str, file_id: str) -> bool:
        return file_id in self._files_cache.get(product_id, [])

    def cache_file(self, product_id: str, file_id: str) -> None:
        if product_id not in self._files_cache:
            self._files_cache[product_id] = set([file_id])
        else:
            self._files_cache[product_id].add(file_id)

    # Recipes


    # Status

    def is_product_downloader(self, url: str) -> bool:
        pass

    def start_product_downloading(self, url: str) -> None:
        pass

    def finish_product_downloading(self, url: str) -> None:
        pass
