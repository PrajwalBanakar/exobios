from abc import ABC, abstractmethod
from uuid import UUID

from app.ingestion.models.chunk import Chunk
from app.ingestion.parsers.base import ParsedPage


class Chunker(ABC):
    """Common interface every chunking strategy implements."""

    @abstractmethod
    def chunk(self, document_id: UUID, pages: list[ParsedPage]) -> list[Chunk]: ...
