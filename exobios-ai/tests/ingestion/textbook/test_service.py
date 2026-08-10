import hashlib
from pathlib import Path
from uuid import uuid4

import fitz
import pytest

from app.ingestion.models.document import (
    ApprovalStatus,
    DocumentMetadata,
    DocumentStatus,
    DocumentType,
    Subject,
)
from app.ingestion.registry.in_memory_registry import InMemoryDocumentRegistry
from app.ingestion.textbook.artifacts import TextbookArtifactWriter
from app.ingestion.textbook.chunker import TextbookChunker
from app.ingestion.textbook.exceptions import (
    DocumentMissingStorageKeyError,
    DocumentNotRegisteredError,
    UnsupportedTextbookFormatError,
)
from app.ingestion.textbook.page_extractor import TextbookPageExtractor
from app.ingestion.textbook.service import TextbookPreparationService
from app.storage.local_storage import LocalDocumentStorage


@pytest.fixture
def storage_root(tmp_path: Path) -> Path:
    root = tmp_path / "source_documents"
    (root / "physiology").mkdir(parents=True)
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "CHAPTER 9 Heart Muscle", fontsize=18)
    page.insert_text(
        (72, 110), "The cardiac cycle is the sequence of events in one heartbeat.", fontsize=10
    )
    content = document.tobytes()
    document.close()
    (root / "physiology" / "book.pdf").write_bytes(content)
    return root


def _service(
    storage_root: Path, extracted_root: Path, processed_root: Path, registry
) -> TextbookPreparationService:
    return TextbookPreparationService(
        registry=registry,
        storage=LocalDocumentStorage(root=storage_root),
        extractor=TextbookPageExtractor(),
        chunker=TextbookChunker(
            target_tokens=50, max_tokens=200, overlap_tokens=10, min_useful_tokens=5
        ),
        artifact_writer=TextbookArtifactWriter(
            extracted_root=extracted_root, processed_root=processed_root
        ),
    )


def _registered_document(storage_root: Path) -> DocumentMetadata:
    content = (storage_root / "physiology" / "book.pdf").read_bytes()
    return DocumentMetadata(
        filename="book.pdf",
        original_path=str(storage_root / "physiology" / "book.pdf"),
        document_type=DocumentType.PDF,
        source="manual-upload",
        checksum=hashlib.sha256(content).hexdigest(),
        title="Physiology",
        subject=Subject.PHYSIOLOGY,
        edition="14th",
        storage_key="physiology/book.pdf",
        approval_status=ApprovalStatus.APPROVED_FOR_POC,
    )


def test_prepare_resolves_document_via_registry_and_storage(tmp_path, storage_root):
    registry = InMemoryDocumentRegistry()
    document = _registered_document(storage_root)
    registry.register(document)
    service = _service(storage_root, tmp_path / "extracted", tmp_path / "processed", registry)

    result = service.prepare(document.id)

    assert result.document.id == document.id
    assert result.summary.total_pdf_pages == 1
    assert len(result.chunks) >= 1
    assert any("cardiac cycle" in c.text.lower() for c in result.chunks)


def test_prepare_raises_when_document_not_registered(tmp_path, storage_root):
    registry = InMemoryDocumentRegistry()
    service = _service(storage_root, tmp_path / "extracted", tmp_path / "processed", registry)

    with pytest.raises(DocumentNotRegisteredError):
        service.prepare(uuid4())


def test_prepare_raises_when_storage_key_missing(tmp_path, storage_root):
    registry = InMemoryDocumentRegistry()
    document = _registered_document(storage_root)
    document.storage_key = None
    registry.register(document)
    service = _service(storage_root, tmp_path / "extracted", tmp_path / "processed", registry)

    with pytest.raises(DocumentMissingStorageKeyError):
        service.prepare(document.id)


def test_prepare_raises_for_non_pdf_document_type(tmp_path, storage_root):
    registry = InMemoryDocumentRegistry()
    document = _registered_document(storage_root)
    document.document_type = DocumentType.TXT
    registry.register(document)
    service = _service(storage_root, tmp_path / "extracted", tmp_path / "processed", registry)

    with pytest.raises(UnsupportedTextbookFormatError):
        service.prepare(document.id)


def test_prepare_does_not_mutate_registry_status(tmp_path, storage_root):
    registry = InMemoryDocumentRegistry()
    document = _registered_document(storage_root)
    registry.register(document)
    service = _service(storage_root, tmp_path / "extracted", tmp_path / "processed", registry)

    service.prepare(document.id)

    reloaded = registry.get(document.id)
    assert reloaded.status == DocumentStatus.PENDING
    assert reloaded.chunk_count == 0


def test_prepare_writes_all_three_artifacts(tmp_path, storage_root):
    registry = InMemoryDocumentRegistry()
    document = _registered_document(storage_root)
    registry.register(document)
    service = _service(storage_root, tmp_path / "extracted", tmp_path / "processed", registry)

    result = service.prepare(document.id)

    assert result.pages_path.is_file()
    assert result.chunks_path.is_file()
    assert result.summary_path.is_file()


def test_prepare_does_not_modify_the_source_pdf(tmp_path, storage_root):
    registry = InMemoryDocumentRegistry()
    document = _registered_document(storage_root)
    registry.register(document)
    service = _service(storage_root, tmp_path / "extracted", tmp_path / "processed", registry)
    original_bytes = (storage_root / "physiology" / "book.pdf").read_bytes()

    service.prepare(document.id)

    assert (storage_root / "physiology" / "book.pdf").read_bytes() == original_bytes


def test_prepare_second_run_produces_identical_chunk_count(tmp_path, storage_root):
    registry = InMemoryDocumentRegistry()
    document = _registered_document(storage_root)
    registry.register(document)
    service = _service(storage_root, tmp_path / "extracted", tmp_path / "processed", registry)

    first = service.prepare(document.id)
    second = service.prepare(document.id)

    assert len(first.chunks) == len(second.chunks)
