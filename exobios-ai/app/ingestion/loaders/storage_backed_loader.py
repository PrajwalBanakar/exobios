from pathlib import Path

from app.ingestion.loaders.base import FileLoader, LoadedFile
from app.storage.interface import DocumentStorage


class StorageBackedFileLoader(FileLoader):
    """FileLoader that resolves `source` as a DocumentStorage key (e.g.
    "physiology/book.pdf") rather than a raw filesystem path.

    This is the seam that lets IngestionService eventually read documents
    through DocumentStorage — local today, object storage later — instead
    of being coupled to LocalFileLoader's direct path access. IngestionService
    already takes its loader as a constructor argument, so a future phase can
    inject `StorageBackedFileLoader(local_storage)` in place of
    `LocalFileLoader()` with no change to IngestionService itself.

    Not wired into any ingestion run in this phase — AI-7A registers
    documents but does not ingest them (see DocumentRegistry/AI-7A scope).
    """

    def __init__(self, storage: DocumentStorage) -> None:
        self._storage = storage

    def load(self, source: str | Path) -> LoadedFile:
        key = str(source)
        content = self._storage.read(key)
        return LoadedFile(content=content, filename=Path(key).name, original_path=key)
