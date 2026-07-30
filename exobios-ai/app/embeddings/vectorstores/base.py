from abc import ABC, abstractmethod
from uuid import UUID

from app.embeddings.models.embedding import EmbeddedChunk
from app.ingestion.models.document import DocumentMetadata


class VectorStore(ABC):
    """Common interface every vector database backend implements. No
    backend-specific types (e.g. qdrant_client models) appear here — swapping
    Qdrant for Pinecone/Weaviate/Milvus/pgvector means adding a new
    VectorStore subclass, with no changes to EmbeddingService or callers."""

    @abstractmethod
    def initialize(self) -> None:
        """Idempotently ensure the backing collection/index exists."""

    @abstractmethod
    def upsert_chunks(
        self, document: DocumentMetadata, embedded_chunks: list[EmbeddedChunk]
    ) -> None: ...

    @abstractmethod
    def delete_document(self, document_id: UUID) -> None: ...

    @abstractmethod
    def document_exists(self, document_id: UUID) -> bool: ...

    @abstractmethod
    def health(self) -> bool: ...
