import threading
from uuid import UUID

from app.ingestion.models.document import ApprovalStatus, DocumentMetadata, DocumentStatus, Subject
from app.ingestion.registry.interface import DocumentRegistry


class InMemoryDocumentRegistry(DocumentRegistry):
    """Process-local registry keyed by document id, with a checksum index
    for O(1) duplicate lookups. Guarded by a lock since FastAPI may run
    sync code from a threadpool."""

    def __init__(self) -> None:
        self._by_id: dict[UUID, DocumentMetadata] = {}
        self._by_checksum: dict[str, UUID] = {}
        self._lock = threading.Lock()

    def register(self, metadata: DocumentMetadata) -> None:
        with self._lock:
            self._by_id[metadata.id] = metadata
            self._by_checksum[metadata.checksum] = metadata.id

    def get(self, document_id: UUID) -> DocumentMetadata | None:
        with self._lock:
            return self._by_id.get(document_id)

    def find_by_checksum(self, checksum: str) -> DocumentMetadata | None:
        with self._lock:
            document_id = self._by_checksum.get(checksum)
            return self._by_id.get(document_id) if document_id else None

    def update(self, metadata: DocumentMetadata) -> None:
        with self._lock:
            if metadata.id not in self._by_id:
                raise KeyError(f"Document {metadata.id} is not registered")
            self._by_id[metadata.id] = metadata
            self._by_checksum[metadata.checksum] = metadata.id

    def list_all(
        self,
        *,
        subject: Subject | None = None,
        approval_status: ApprovalStatus | None = None,
        ingestion_status: DocumentStatus | None = None,
    ) -> list[DocumentMetadata]:
        with self._lock:
            documents = list(self._by_id.values())

        if subject is not None:
            documents = [doc for doc in documents if doc.subject == subject]
        if approval_status is not None:
            documents = [doc for doc in documents if doc.approval_status == approval_status]
        if ingestion_status is not None:
            documents = [doc for doc in documents if doc.status == ingestion_status]
        return documents
