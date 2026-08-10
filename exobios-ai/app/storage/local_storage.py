from pathlib import Path

from app.storage.exceptions import DocumentNotFoundError, InvalidStorageKeyError
from app.storage.interface import DocumentStorage


class LocalDocumentStorage(DocumentStorage):
    """DocumentStorage backed by a confined local directory.

    Every key is resolved relative to `root` and verified to still be
    inside it after resolution — an absolute key, or a relative key that
    escapes via `..`, is rejected as InvalidStorageKeyError rather than
    silently reading outside the storage root.
    """

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).resolve()

    @property
    def root(self) -> Path:
        return self._root

    def read(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.is_file():
            raise DocumentNotFoundError(key=key)
        return path.read_bytes()

    def exists(self, key: str) -> bool:
        try:
            path = self._resolve(key)
        except InvalidStorageKeyError:
            return False
        return path.is_file()

    def list(self, prefix: str | None = None) -> list[str]:
        base = self._resolve(prefix) if prefix else self._root
        if not base.exists():
            return []
        return sorted(
            path.relative_to(self._root).as_posix() for path in base.rglob("*") if path.is_file()
        )

    def _resolve(self, key: str) -> Path:
        if not key or Path(key).is_absolute():
            raise InvalidStorageKeyError(key=key)
        candidate = (self._root / key).resolve()
        if candidate != self._root and not candidate.is_relative_to(self._root):
            raise InvalidStorageKeyError(key=key)
        return candidate
