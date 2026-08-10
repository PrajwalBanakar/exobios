from abc import ABC, abstractmethod
from uuid import UUID

from app.embeddings.models.embedding import EmbeddedChunk, VectorMatch
from app.ingestion.models.document import DocumentMetadata


class VectorStore(ABC):
    """Common interface every vector database backend implements. No
    backend-specific types (e.g. qdrant_client models) appear here — swapping
    Qdrant for Pinecone/Weaviate/Milvus/pgvector means adding a new
    VectorStore subclass, with no changes to EmbeddingService, Retriever, or
    other callers."""

    @abstractmethod
    def initialize(self) -> None:
        """Idempotently ensure the backing collection/index exists."""

    @abstractmethod
    def upsert_chunks(
        self, document: DocumentMetadata, embedded_chunks: list[EmbeddedChunk]
    ) -> None: ...

    @abstractmethod
    def upsert_raw(self, points: list[tuple[str, list[float], dict[str, object]]]) -> None:
        """Upsert (id, vector, payload) tuples directly, bypassing the
        Chunk/DocumentMetadata-shaped upsert_chunks() — for producers whose
        payload doesn't fit that shape (e.g. textbook chunks, whose richer
        metadata — subject, chapter, printed page — has no equivalent on the
        generic ingestion Chunk model). Plain tuples/dicts, not qdrant_client
        types, to keep this interface backend-independent."""

    @abstractmethod
    def delete_document(self, document_id: UUID) -> None: ...

    @abstractmethod
    def document_exists(self, document_id: UUID) -> bool: ...

    @abstractmethod
    def count_for_document(self, document_id: UUID) -> int:
        """Number of points currently stored for a document — the basis for
        idempotent ingestion (compare against the expected chunk count
        rather than trusting a boolean "some vectors exist")."""

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
        min_score: float | None = None,
        filters: dict[str, object] | None = None,
    ) -> list[VectorMatch]:
        """Cosine-similarity search for the `top_k` nearest points, optionally
        filtered to those scoring at least `min_score` and/or matching every
        key/value in `filters` (exact-match AND semantics)."""

    @abstractmethod
    def health(self) -> bool: ...
