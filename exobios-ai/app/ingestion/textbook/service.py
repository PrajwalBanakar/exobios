import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median
from uuid import UUID

from app.ingestion.loaders.storage_backed_loader import StorageBackedFileLoader
from app.ingestion.models.document import DocumentMetadata, DocumentType
from app.ingestion.registry.interface import DocumentRegistry
from app.ingestion.textbook.artifacts import TextbookArtifactWriter
from app.ingestion.textbook.chunker import TextbookChunker
from app.ingestion.textbook.exceptions import (
    DocumentMissingStorageKeyError,
    DocumentNotRegisteredError,
    UnsupportedTextbookFormatError,
)
from app.ingestion.textbook.models import (
    ExtractionStatus,
    PageExtraction,
    ProcessingSummary,
    TextbookChunk,
)
from app.ingestion.textbook.page_extractor import TextbookPageExtractor
from app.storage.interface import DocumentStorage

logger = logging.getLogger("app.ingestion.textbook")


def _percentile(values: list[int], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * (pct / 100)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return float(ordered[lower])
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


@dataclass
class TextbookPreparationResult:
    document: DocumentMetadata
    pages: list[PageExtraction]
    chunks: list[TextbookChunk]
    summary: ProcessingSummary
    pages_path: Path
    chunks_path: Path
    summary_path: Path


class TextbookPreparationService:
    """Orchestrates document_id -> DocumentRegistry -> storage_key ->
    DocumentStorage -> StorageBackedFileLoader -> TextbookPageExtractor ->
    TextbookChunker -> artifacts.

    Dry-run only: never calls an embedding provider, never touches Qdrant,
    never calls an LLM, and never mutates the registry — a document
    registered in AI-7A is left exactly PENDING/untouched here. AI-7C
    decides what "ingested" means once embeddings actually happen.
    """

    def __init__(
        self,
        registry: DocumentRegistry,
        storage: DocumentStorage,
        extractor: TextbookPageExtractor,
        chunker: TextbookChunker,
        artifact_writer: TextbookArtifactWriter,
    ) -> None:
        self._registry = registry
        self._storage = storage
        self._extractor = extractor
        self._chunker = chunker
        self._artifacts = artifact_writer

    def prepare(self, document_id: UUID) -> TextbookPreparationResult:
        start = time.perf_counter()
        document = self._resolve_document(document_id)

        loader = StorageBackedFileLoader(storage=self._storage)
        loaded = loader.load(document.storage_key)

        logger.info(
            "textbook_extraction_started document_id=%s storage_key=%s",
            document_id,
            document.storage_key,
        )
        extraction = self._extractor.extract(document_id, loaded.content)
        logger.info(
            "textbook_extraction_completed document_id=%s pdf_pages=%s blocks=%s",
            document_id,
            len(extraction.pages),
            len(extraction.blocks),
        )

        chunks = self._chunker.chunk(
            document_id=document_id,
            subject=document.subject,
            title=document.title,
            edition=document.edition,
            blocks=extraction.blocks,
        )
        logger.info(
            "textbook_chunking_completed document_id=%s chunks=%s", document_id, len(chunks)
        )

        summary = self._build_summary(document, extraction.pages, chunks)

        pages_path = self._artifacts.write_pages(document_id, extraction.pages)
        chunks_path = self._artifacts.write_chunks(document_id, chunks)
        summary_path = self._artifacts.write_summary(document_id, summary)

        elapsed = round(time.perf_counter() - start, 2)
        logger.info(
            "textbook_preparation_completed document_id=%s elapsed_seconds=%s", document_id, elapsed
        )

        return TextbookPreparationResult(
            document=document,
            pages=extraction.pages,
            chunks=chunks,
            summary=summary,
            pages_path=pages_path,
            chunks_path=chunks_path,
            summary_path=summary_path,
        )

    def _resolve_document(self, document_id: UUID) -> DocumentMetadata:
        document = self._registry.get(document_id)
        if document is None:
            raise DocumentNotRegisteredError(document_id=document_id)
        if not document.storage_key:
            raise DocumentMissingStorageKeyError(document_id=document_id)
        if document.document_type != DocumentType.PDF:
            raise UnsupportedTextbookFormatError(
                document_id=document_id, document_type=document.document_type.value
            )
        return document

    def _build_summary(
        self, document: DocumentMetadata, pages: list[PageExtraction], chunks: list[TextbookChunk]
    ) -> ProcessingSummary:
        token_counts = [chunk.metadata.token_count for chunk in chunks]
        chapters = {
            chunk.metadata.chapter_number for chunk in chunks if chunk.metadata.chapter_number
        }

        status_counts = {status: 0 for status in ExtractionStatus}
        for page in pages:
            status_counts[page.extraction_status] += 1

        return ProcessingSummary(
            document_id=document.id,
            title=document.title,
            subject=document.subject,
            total_pdf_pages=len(pages),
            pages_with_text=status_counts[ExtractionStatus.TEXT_OK],
            sparse_pages=status_counts[ExtractionStatus.TEXT_SPARSE],
            possible_scanned_pages=status_counts[ExtractionStatus.POSSIBLE_SCAN],
            extraction_failed_pages=status_counts[ExtractionStatus.EXTRACTION_FAILED],
            chapters_detected=len(chapters),
            chunks_created=len(chunks),
            min_tokens=min(token_counts) if token_counts else 0,
            max_tokens=max(token_counts) if token_counts else 0,
            mean_tokens=round(mean(token_counts), 1) if token_counts else 0.0,
            median_tokens=round(median(token_counts), 1) if token_counts else 0.0,
            p95_tokens=round(_percentile(token_counts, 95), 1),
            oversized_chunks=sum(1 for t in token_counts if t > self._chunker.max_tokens),
            undersized_chunks=sum(1 for t in token_counts if t < self._chunker.min_useful_tokens),
            generated_at=datetime.now(UTC),
        )
