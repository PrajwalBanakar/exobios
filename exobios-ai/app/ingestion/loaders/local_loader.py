from pathlib import Path

from app.ingestion.loaders.base import FileLoader, LoadedFile


class LocalFileLoader(FileLoader):
    """Loads files from the local filesystem."""

    def load(self, source: str | Path) -> LoadedFile:
        path = Path(source)
        content = path.read_bytes()
        return LoadedFile(content=content, filename=path.name, original_path=str(path))
