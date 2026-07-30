from abc import ABC, abstractmethod
from uuid import UUID

from app.ingestion.models.document import DocumentMetadata


class DocumentRegistry(ABC):
    """Storage for document metadata. Swap the in-memory implementation for
    a PostgreSQL-backed one by implementing this interface — no caller
    changes, since IngestionService depends only on this abstraction."""

    @abstractmethod
    def register(self, metadata: DocumentMetadata) -> None: ...

    @abstractmethod
    def get(self, document_id: UUID) -> DocumentMetadata | None: ...

    @abstractmethod
    def find_by_checksum(self, checksum: str) -> DocumentMetadata | None: ...

    @abstractmethod
    def update(self, metadata: DocumentMetadata) -> None: ...

    @abstractmethod
    def list_all(self) -> list[DocumentMetadata]: ...
