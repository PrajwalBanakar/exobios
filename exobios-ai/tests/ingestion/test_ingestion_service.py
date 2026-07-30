import hashlib
from pathlib import Path

import pytest

from app.ingestion.chunkers.recursive_chunker import RecursiveChunker
from app.ingestion.cleaning.text_cleaner import TextCleaner
from app.ingestion.exceptions import DuplicateDocument, UnsupportedDocumentType
from app.ingestion.loaders.local_loader import LocalFileLoader
from app.ingestion.models.document import DocumentStatus
from app.ingestion.parsers.registry import ParserRegistry
from app.ingestion.registry.in_memory_registry import InMemoryDocumentRegistry
from app.ingestion.services.factory import build_default_ingestion_service
from app.ingestion.services.ingestion_service import IngestionService


def test_ingest_txt_file_end_to_end(tmp_path: Path, fake_embedding_service):
    file_path = tmp_path / "note.txt"
    content = "Patient reports fever and cough.\n\n" * 100
    # write_bytes (not write_text) so the on-disk bytes exactly match
    # content.encode() below — write_text applies platform newline translation.
    file_path.write_bytes(content.encode("utf-8"))

    service = build_default_ingestion_service(
        fake_embedding_service, chunk_size=200, chunk_overlap=20
    )
    result = service.ingest(file_path, source="unit-test", tags=["intake"], language="en")

    assert result.document.status == DocumentStatus.COMPLETED
    assert result.document.page_count == 1
    assert result.document.chunk_count == len(result.chunks)
    assert result.document.checksum == hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert result.document.tags == ["intake"]
    assert result.document.language == "en"
    assert len(result.chunks) > 1
    assert all(c.metadata.document_id == result.document.id for c in result.chunks)

    # Embedding must run, with the exact chunks produced, before the pipeline
    # is considered complete.
    assert len(fake_embedding_service.calls) == 1
    embedded_document, embedded_chunks = fake_embedding_service.calls[0]
    assert embedded_document.id == result.document.id
    assert embedded_chunks == result.chunks


def test_checksum_generation_is_deterministic_for_identical_content(
    tmp_path: Path, fake_embedding_service
):
    file_path = tmp_path / "note.txt"
    content = "identical content"
    file_path.write_bytes(content.encode("utf-8"))
    expected_checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()

    service = build_default_ingestion_service(fake_embedding_service)
    result = service.ingest(file_path, source="unit-test")

    assert result.document.checksum == expected_checksum


def test_duplicate_content_is_rejected_even_under_a_different_filename(
    tmp_path: Path, fake_embedding_service
):
    first_path = tmp_path / "a.txt"
    first_path.write_text("Same content", encoding="utf-8")
    second_path = tmp_path / "b.txt"
    second_path.write_text("Same content", encoding="utf-8")

    service = build_default_ingestion_service(fake_embedding_service)
    first_result = service.ingest(first_path, source="unit-test")

    with pytest.raises(DuplicateDocument) as exc_info:
        service.ingest(second_path, source="unit-test")

    assert exc_info.value.existing_document_id == first_result.document.id
    # Duplicate detection happens before embedding, so only the first
    # ingestion should have triggered an embedding call.
    assert len(fake_embedding_service.calls) == 1


def test_unsupported_extension_raises(tmp_path: Path, fake_embedding_service):
    file_path = tmp_path / "data.csv"
    file_path.write_text("a,b,c", encoding="utf-8")

    service = build_default_ingestion_service(fake_embedding_service)

    with pytest.raises(UnsupportedDocumentType):
        service.ingest(file_path, source="unit-test")

    assert fake_embedding_service.calls == []


def test_document_is_registered_and_retrievable(tmp_path: Path, fake_embedding_service):
    file_path = tmp_path / "note.txt"
    file_path.write_text("Registered content", encoding="utf-8")
    registry = InMemoryDocumentRegistry()
    service = IngestionService(
        loader=LocalFileLoader(),
        parser_registry=ParserRegistry(),
        cleaner=TextCleaner(),
        chunker=RecursiveChunker(),
        registry=registry,
        embedding_service=fake_embedding_service,
    )

    result = service.ingest(file_path, source="unit-test")

    registered = registry.get(result.document.id)
    assert registered is not None
    assert registered.checksum == result.document.checksum
