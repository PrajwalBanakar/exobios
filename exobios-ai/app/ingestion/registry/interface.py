from abc import ABC, abstractmethod
from uuid import UUID

from app.ingestion.models.document import ApprovalStatus, DocumentMetadata, DocumentStatus, Subject


class DocumentRegistry(ABC):
    """Storage for document metadata. Swap the in-memory implementation for
    a SQLite- or PostgreSQL-backed one by implementing this interface — no
    caller changes, since IngestionService (and the registration workflow)
    depend only on this abstraction."""

    @abstractmethod
    def register(self, metadata: DocumentMetadata) -> None: ...

    @abstractmethod
    def get(self, document_id: UUID) -> DocumentMetadata | None: ...

    @abstractmethod
    def find_by_checksum(self, checksum: str) -> DocumentMetadata | None: ...

    @abstractmethod
    def update(self, metadata: DocumentMetadata) -> None: ...

    @abstractmethod
    def list_all(
        self,
        *,
        subject: Subject | None = None,
        approval_status: ApprovalStatus | None = None,
        ingestion_status: DocumentStatus | None = None,
    ) -> list[DocumentMetadata]:
        """List registered documents, optionally narrowed by exact-match
        filters on subject / approval_status / ingestion_status. Deliberately
        just three keyword filters, not a generic query DSL — add another
        named filter here only when a real caller needs one, in the same
        spirit as everything else in this interface."""
        ...
