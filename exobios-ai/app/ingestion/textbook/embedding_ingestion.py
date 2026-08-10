import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from app.embeddings.exceptions import EmbeddingGenerationError
from app.embeddings.providers.base import EmbeddingProvider
from app.embeddings.vectorstores.base import VectorStore
from app.ingestion.models.document import DocumentMetadata, DocumentStatus
from app.ingestion.registry.interface import DocumentRegistry
from app.ingestion.textbook.artifacts import TextbookArtifactWriter
from app.ingestion.textbook.exceptions import (
    DocumentMissingStorageKeyError,
    DocumentNotRegisteredError,
)
from app.ingestion.textbook.models import TextbookChunk

logger = logging.getLogger("app.ingestion.textbook.embedding")

ProgressCallback = Callable[[str], None]


@dataclass
class TextbookEmbeddingIngestionResult:
    document_id: UUID
    title: str | None
    status: DocumentStatus
    chunks_total: int
    chunks_embedded: int
    skipped: bool
    error: str | None = None


class TextbookEmbeddingIngestionService:
    """Reads AI-7B's already-validated chunks.jsonl for a registered
    document (never re-extracts/re-chunks the PDF), embeds them via the
    existing EmbeddingProvider abstraction — whichever of OpenAI/Gemini is
    configured, unchanged — and stores them in the dedicated textbook Qdrant
    collection via VectorStore.upsert_raw().

    Idempotent by design: before embedding, compares Qdrant's actual point
    count for the document against the expected chunk count — never just
    "some vectors exist", which breaks once a collection holds multiple
    documents. A short count means an incomplete prior run (or none at
    all) and is cleared and re-embedded from scratch; a matching count
    means already fully embedded, and is skipped unless force=True.
    """

    def __init__(
        self,
        registry: DocumentRegistry,
        artifact_reader: TextbookArtifactWriter,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
        embedding_batch_size: int,
        max_retries: int = 6,
        batch_pacing_seconds: float = 1.0,
    ) -> None:
        self._registry = registry
        self._artifacts = artifact_reader
        self._provider = embedding_provider
        self._vector_store = vector_store
        self._batch_size = max(1, embedding_batch_size)
        self._max_retries = max(1, max_retries)
        # A small pause between successful batches spreads requests out
        # rather than bursting them — real free-tier embedding quotas
        # (observed: Gemini's embed_content free tier, 100 req/min) can be
        # exhausted by back-to-back large batches even without any single
        # request failing on its own.
        self._batch_pacing_seconds = max(0.0, batch_pacing_seconds)

    def ingest(
        self,
        document_id: UUID,
        *,
        force: bool = False,
        progress: ProgressCallback | None = None,
    ) -> TextbookEmbeddingIngestionResult:
        report = progress or (lambda _message: None)

        document = self._registry.get(document_id)
        if document is None:
            raise DocumentNotRegisteredError(document_id=document_id)
        if not document.storage_key:
            raise DocumentMissingStorageKeyError(document_id=document_id)

        label = document.title or document.filename
        chunks = self._artifacts.read_chunks(document_id)
        expected = len(chunks)

        existing_count = self._vector_store.count_for_document(document_id)
        if expected > 0 and existing_count == expected and not force:
            report(f"{label}: already fully embedded ({expected} chunks) — skipping (use --force)")
            return TextbookEmbeddingIngestionResult(
                document_id=document_id,
                title=document.title,
                status=document.status,
                chunks_total=expected,
                chunks_embedded=existing_count,
                skipped=True,
            )

        if existing_count > 0:
            report(
                f"{label}: found {existing_count}/{expected} existing vectors "
                f"(incomplete prior run or --force) — clearing before re-embedding"
            )
            self._vector_store.delete_document(document_id)

        self._set_status(document, DocumentStatus.PROCESSING)
        logger.info(
            "textbook_embedding_started document_id=%s expected_chunks=%s", document_id, expected
        )

        try:
            self._embed_and_store(document, chunks, label, report)
        except Exception as exc:
            logger.error("textbook_embedding_failed document_id=%s reason=%s", document_id, exc)
            self._set_status(document, DocumentStatus.FAILED)
            report(f"{label}: FAILED — {exc}")
            return TextbookEmbeddingIngestionResult(
                document_id=document_id,
                title=document.title,
                status=DocumentStatus.FAILED,
                chunks_total=expected,
                chunks_embedded=self._vector_store.count_for_document(document_id),
                skipped=False,
                error=str(exc),
            )

        final_count = self._vector_store.count_for_document(document_id)
        if final_count != expected:
            error = f"expected {expected} vectors, found {final_count} after upsert"
            self._set_status(document, DocumentStatus.FAILED)
            report(f"{label}: FAILED — {error}")
            return TextbookEmbeddingIngestionResult(
                document_id=document_id,
                title=document.title,
                status=DocumentStatus.FAILED,
                chunks_total=expected,
                chunks_embedded=final_count,
                skipped=False,
                error=error,
            )

        document.chunk_count = final_count
        self._set_status(document, DocumentStatus.COMPLETED)
        report(f"{label}: COMPLETED ({final_count} chunks embedded)")
        logger.info(
            "textbook_embedding_completed document_id=%s chunks_embedded=%s",
            document_id,
            final_count,
        )
        return TextbookEmbeddingIngestionResult(
            document_id=document_id,
            title=document.title,
            status=DocumentStatus.COMPLETED,
            chunks_total=expected,
            chunks_embedded=final_count,
            skipped=False,
        )

    def _embed_and_store(
        self,
        document: DocumentMetadata,
        chunks: list[TextbookChunk],
        label: str,
        report: ProgressCallback,
    ) -> None:
        total_batches = max(1, (len(chunks) + self._batch_size - 1) // self._batch_size)
        stored = 0
        for batch_index in range(total_batches):
            start = batch_index * self._batch_size
            batch = chunks[start : start + self._batch_size]
            if not batch:
                continue

            report(f"{label}: embedding batch {batch_index + 1}/{total_batches}...")
            vectors = self._embed_with_retry([chunk.text for chunk in batch])

            points = [
                (str(chunk.metadata.chunk_id), vector, self._build_payload(document, chunk))
                for chunk, vector in zip(batch, vectors, strict=True)
            ]
            self._vector_store.upsert_raw(points)
            stored += len(points)
            report(f"{label}: stored {stored}/{len(chunks)} chunks")

            if self._batch_pacing_seconds and batch_index + 1 < total_batches:
                time.sleep(self._batch_pacing_seconds)

    def _embed_with_retry(self, texts: list[str]) -> list[list[float]]:
        last_error: EmbeddingGenerationError | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                return self._provider.embed_batch(texts)
            except EmbeddingGenerationError as exc:
                last_error = exc
                if attempt < self._max_retries:
                    # Capped, not purely exponential: a per-minute quota
                    # (observed: Gemini's free-tier embed_content limit)
                    # needs waits long enough to actually cross into the
                    # next window, not just a few seconds of backoff.
                    wait_seconds = min(60, 2**attempt)
                    logger.warning(
                        "textbook_embedding_batch_retry attempt=%s wait_seconds=%s reason=%s",
                        attempt,
                        wait_seconds,
                        exc,
                    )
                    time.sleep(wait_seconds)
        assert last_error is not None  # noqa: S101 - loop always sets it before exhausting retries
        raise last_error

    def _build_payload(self, document: DocumentMetadata, chunk: TextbookChunk) -> dict[str, object]:
        meta = chunk.metadata
        return {
            "document_id": str(document.id),
            "document_checksum": document.checksum,
            "chunk_id": str(meta.chunk_id),
            "text": chunk.text,
            "subject": meta.subject.value if meta.subject else None,
            "title": meta.title,
            "edition": meta.edition,
            "unit_or_section": meta.unit_or_section,
            "chapter_number": meta.chapter_number,
            "chapter_title": meta.chapter_title,
            "section_title": meta.section_title,
            "subsection_title": meta.subsection_title,
            "pdf_page_start": meta.pdf_page_start,
            "pdf_page_end": meta.pdf_page_end,
            "printed_page_start": meta.printed_page_start,
            "printed_page_end": meta.printed_page_end,
            "chunk_index": meta.chunk_index,
            "token_count": meta.token_count,
            "page_classification": meta.page_classification.value,
            # RetrievedChunk-required fields TextbookChunkMetadata doesn't
            # carry itself — pulled from the parent document instead.
            "page_number": meta.pdf_page_start,
            "document_type": document.document_type.value,
            "filename": document.filename,
            "language": document.language,
            "tags": document.tags,
            "version": document.version,
            "source": document.source,
        }

    def _set_status(self, document: DocumentMetadata, status: DocumentStatus) -> None:
        document.status = status
        self._registry.update(document)
