import logging
import time

from app.embeddings.exceptions import EmbeddingGenerationError, VectorStoreError
from app.embeddings.models.embedding import EmbeddedChunk, EmbeddingVector
from app.embeddings.providers.base import EmbeddingProvider
from app.embeddings.vectorstores.base import VectorStore
from app.ingestion.models.chunk import Chunk
from app.ingestion.models.document import DocumentMetadata

logger = logging.getLogger("app.embeddings")


class EmbeddingService:
    """Generates embeddings for a document's chunks and persists them.

    Depends only on EmbeddingProvider and VectorStore interfaces — it has no
    knowledge of OpenAI or Qdrant specifically, so either can be swapped
    independently of this class.
    """

    def __init__(self, provider: EmbeddingProvider, vector_store: VectorStore) -> None:
        self._provider = provider
        self._vector_store = vector_store

    def embed_document(self, document: DocumentMetadata, chunks: list[Chunk]) -> int:
        start = time.perf_counter()
        logger.info("embedding_started document_id=%s chunk_count=%s", document.id, len(chunks))

        if not chunks:
            logger.info(
                "embedding_completed document_id=%s chunk_count=0 elapsed_ms=0", document.id
            )
            return 0

        embedded_chunks = self._embed_chunks(document, chunks)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "embedding_completed document_id=%s chunk_count=%s elapsed_ms=%s",
            document.id,
            len(chunks),
            elapsed_ms,
        )

        self._upsert_chunks(document, embedded_chunks)

        return len(embedded_chunks)

    def _embed_chunks(
        self, document: DocumentMetadata, chunks: list[Chunk]
    ) -> list[EmbeddedChunk]:
        try:
            vectors = self._provider.embed_batch([chunk.text for chunk in chunks])
        except EmbeddingGenerationError:
            logger.error("embedding_failed document_id=%s stage=embedding", document.id)
            raise
        except Exception as exc:
            logger.error("embedding_failed document_id=%s stage=embedding", document.id)
            raise EmbeddingGenerationError(reason=str(exc)) from exc

        return [
            EmbeddedChunk(
                chunk=chunk,
                vector=EmbeddingVector(
                    values=vector, model=self._provider.model, dimensions=len(vector)
                ),
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]

    def _upsert_chunks(
        self, document: DocumentMetadata, embedded_chunks: list[EmbeddedChunk]
    ) -> None:
        upsert_start = time.perf_counter()
        logger.info(
            "vectorstore_upsert_started document_id=%s chunk_count=%s",
            document.id,
            len(embedded_chunks),
        )

        try:
            self._vector_store.upsert_chunks(document, embedded_chunks)
        except VectorStoreError:
            logger.error("vectorstore_upsert_failed document_id=%s", document.id)
            raise
        except Exception as exc:
            logger.error("vectorstore_upsert_failed document_id=%s", document.id)
            raise VectorStoreError(reason=str(exc)) from exc

        elapsed_ms = round((time.perf_counter() - upsert_start) * 1000, 2)
        logger.info(
            "vectorstore_upsert_completed document_id=%s chunk_count=%s elapsed_ms=%s",
            document.id,
            len(embedded_chunks),
            elapsed_ms,
        )
