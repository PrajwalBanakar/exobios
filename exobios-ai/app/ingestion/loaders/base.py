from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel


class LoadedFile(BaseModel):
    """Raw bytes plus enough provenance to build a DocumentMetadata record."""

    content: bytes
    filename: str
    original_path: str


class FileLoader(ABC):
    """Source-agnostic file access. Implement this to add new sources
    (e.g. S3, a URL fetcher) without touching the ingestion service."""

    @abstractmethod
    def load(self, source: str | Path) -> LoadedFile: ...
