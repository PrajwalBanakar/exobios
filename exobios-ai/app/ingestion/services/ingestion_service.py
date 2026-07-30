import hashlib
import logging
import time
from pathlib import Path

from app.ingestion.chunkers.base import Chunker
from app.ingestion.cleaning.text_cleaner import TextCleaner
from app.ingestion.exceptions import (
    ChunkingError,
    DocumentParseError,
    DuplicateDocument,
    UnsupportedDocumentType,
)
from app.ingestion.loaders.base import FileLoader
from app.ingestion.models.document import DocumentMetadata, DocumentStatus, detect_document_type
from app.ingestion.models.result import IngestionResult
from app.ingestion.parsers.registry import ParserRegistry
from app.ingestion.registry.interface import DocumentRegistry

logger = logging.getLogger("app.ingestion")


class IngestionService:
    """Orchestrates: load -> parse -> clean -> chunk -> register.

    Every collaborator is injected as an interface (FileLoader, ParserRegistry,
    TextCleaner, Chunker, DocumentRegistry), so this class has no knowledge of
    PDF/DOCX specifics, storage backend, or chunking strategy — each can be
    swapped independently.
    """

    def __init__(
        self,
        loader: FileLoader,
        parser_registry: ParserRegistry,
        cleaner: TextCleaner,
        chunker: Chunker,
        registry: DocumentRegistry,
    ) -> None:
        self._loader = loader
        self._parser_registry = parser_registry
        self._cleaner = cleaner
        self._chunker = chunker
        self._registry = registry

    def ingest(
        self,
        path: str | Path,
        *,
        source: str,
        version: str = "1.0",
        tags: list[str] | None = None,
        language: str | None = None,
    ) -> IngestionResult:
        start = time.perf_counter()
        loaded = self._loader.load(path)
        checksum = hashlib.sha256(loaded.content).hexdigest()
        logger.info("ingestion_started filename=%s checksum=%s", loaded.filename, checksum)

        existing = self._registry.find_by_checksum(checksum)
        if existing is not None:
            logger.warning(
                "ingestion_duplicate filename=%s checksum=%s existing_document_id=%s",
                loaded.filename,
                checksum,
                existing.id,
            )
            raise DuplicateDocument(checksum=checksum, existing_document_id=existing.id)

        document_type = detect_document_type(loaded.filename)
        if document_type is None:
            logger.error("ingestion_failed filename=%s stage=type_detection", loaded.filename)
            raise UnsupportedDocumentType(filename=loaded.filename)

        parser = self._parser_registry.get_parser(document_type)
        try:
            parsed = parser.parse(loaded.content, loaded.filename)
        except DocumentParseError:
            logger.error("ingestion_failed filename=%s stage=parsing", loaded.filename)
            raise
        except Exception as exc:
            logger.error("ingestion_failed filename=%s stage=parsing", loaded.filename)
            raise DocumentParseError(filename=loaded.filename, reason=str(exc)) from exc

        logger.info(
            "parsing_completed filename=%s document_type=%s page_count=%s",
            loaded.filename,
            document_type,
            len(parsed.pages),
        )

        cleaned_pages = self._cleaner.clean_pages(parsed.pages)

        metadata = DocumentMetadata(
            filename=loaded.filename,
            original_path=loaded.original_path,
            document_type=document_type,
            source=source,
            version=version,
            checksum=checksum,
            status=DocumentStatus.PROCESSING,
            page_count=len(cleaned_pages),
            tags=tags or [],
            language=language,
        )

        try:
            chunks = self._chunker.chunk(metadata.id, cleaned_pages)
        except ChunkingError:
            logger.error("ingestion_failed document_id=%s stage=chunking", metadata.id)
            raise
        except Exception as exc:
            logger.error("ingestion_failed document_id=%s stage=chunking", metadata.id)
            raise ChunkingError(document_id=metadata.id, reason=str(exc)) from exc

        logger.info("chunking_completed document_id=%s chunk_count=%s", metadata.id, len(chunks))

        metadata.chunk_count = len(chunks)
        metadata.status = DocumentStatus.COMPLETED
        self._registry.register(metadata)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "ingestion_completed document_id=%s filename=%s page_count=%s chunk_count=%s "
            "checksum=%s elapsed_ms=%s",
            metadata.id,
            loaded.filename,
            metadata.page_count,
            metadata.chunk_count,
            checksum,
            elapsed_ms,
        )

        return IngestionResult(document=metadata, chunks=chunks)
