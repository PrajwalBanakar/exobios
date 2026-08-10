from pathlib import Path
from uuid import uuid4

import pytest

from app.embeddings.exceptions import EmbeddingGenerationError
from app.ingestion.exceptions import IngestionError
from app.ingestion.models.document import (
    ApprovalStatus,
    DocumentMetadata,
    DocumentStatus,
    DocumentType,
    Subject,
)
from app.ingestion.registry.in_memory_registry import InMemoryDocumentRegistry
from app.ingestion.textbook.artifacts import TextbookArtifactWriter
from app.ingestion.textbook.embedding_ingestion import TextbookEmbeddingIngestionService
from app.ingestion.textbook.models import (
    PageClassification,
    TextbookChunk,
    TextbookChunkMetadata,
)


class FakeEmbeddingProvider:
    def __init__(self, dimensions: int = 3, fail_times: int = 0) -> None:
        self.dimensions = dimensions
        self.fail_times = fail_times
        self.calls: list[list[str]] = []

    @property
    def model(self) -> str:
        return "fake-embedding-model"

    def embed_text(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self.fail_times > 0:
            self.fail_times -= 1
            raise EmbeddingGenerationError(reason="simulated transient failure")
        self.calls.append(list(texts))
        return [[float(len(text))] * self.dimensions for text in texts]


class FakeVectorStore:
    def __init__(self) -> None:
        self.points: dict[str, tuple[list[float], dict]] = {}
        self.upsert_calls = 0
        self.deleted_documents: list = []

    def upsert_raw(self, points) -> None:
        self.upsert_calls += 1
        for point_id, vector, payload in points:
            self.points[point_id] = (vector, payload)

    def count_for_document(self, document_id) -> int:
        return sum(
            1 for _, payload in self.points.values() if payload["document_id"] == str(document_id)
        )

    def delete_document(self, document_id) -> None:
        self.deleted_documents.append(document_id)
        to_remove = [
            pid for pid, (_, p) in self.points.items() if p["document_id"] == str(document_id)
        ]
        for pid in to_remove:
            del self.points[pid]


def _document(**overrides) -> DocumentMetadata:
    defaults = {
        "filename": "physiology.pdf",
        "original_path": "physiology/book.pdf",
        "document_type": DocumentType.PDF,
        "source": "manual-upload",
        "checksum": "abc123",
        "title": "Physiology",
        "subject": Subject.PHYSIOLOGY,
        "storage_key": "physiology/book.pdf",
        "approval_status": ApprovalStatus.APPROVED_FOR_POC,
    }
    defaults.update(overrides)
    return DocumentMetadata(**defaults)


def _chunk(document_id, chunk_index: int, text: str = "The cardiac cycle...") -> TextbookChunk:
    return TextbookChunk(
        text=text,
        metadata=TextbookChunkMetadata(
            document_id=document_id,
            subject=Subject.PHYSIOLOGY,
            title="Physiology",
            edition=None,
            unit_or_section=None,
            chapter_number="9",
            chapter_title="Heart Muscle",
            section_title=None,
            subsection_title=None,
            pdf_page_start=117,
            pdf_page_end=117,
            printed_page_start=None,
            printed_page_end=None,
            chunk_index=chunk_index,
            token_count=10,
            page_classification=PageClassification.MAIN_CONTENT,
        ),
    )


@pytest.fixture
def artifacts(tmp_path: Path) -> TextbookArtifactWriter:
    return TextbookArtifactWriter(
        extracted_root=tmp_path / "extracted", processed_root=tmp_path / "processed"
    )


def _service(registry, artifacts, provider=None, vector_store=None, batch_size=2):
    return TextbookEmbeddingIngestionService(
        registry=registry,
        artifact_reader=artifacts,
        embedding_provider=provider or FakeEmbeddingProvider(),
        vector_store=vector_store or FakeVectorStore(),
        embedding_batch_size=batch_size,
        batch_pacing_seconds=0,  # keep tests fast — pacing is a real-quota concern, not a test one
    )


def test_ingest_embeds_all_chunks_and_marks_completed(artifacts):
    registry = InMemoryDocumentRegistry()
    document = _document()
    registry.register(document)
    chunks = [_chunk(document.id, i) for i in range(5)]
    artifacts.write_chunks(document.id, chunks)
    vector_store = FakeVectorStore()
    service = _service(registry, artifacts, vector_store=vector_store)

    result = service.ingest(document.id)

    assert result.status == DocumentStatus.COMPLETED
    assert result.chunks_total == 5
    assert result.chunks_embedded == 5
    assert registry.get(document.id).status == DocumentStatus.COMPLETED
    assert registry.get(document.id).chunk_count == 5


def test_ingest_batches_according_to_batch_size(artifacts):
    registry = InMemoryDocumentRegistry()
    document = _document()
    registry.register(document)
    chunks = [_chunk(document.id, i) for i in range(5)]
    artifacts.write_chunks(document.id, chunks)
    provider = FakeEmbeddingProvider()
    service = _service(registry, artifacts, provider=provider, batch_size=2)

    service.ingest(document.id)

    # 5 chunks / batch_size=2 -> batches of 2, 2, 1
    assert [len(call) for call in provider.calls] == [2, 2, 1]


def test_ingest_reports_progress(artifacts):
    registry = InMemoryDocumentRegistry()
    document = _document()
    registry.register(document)
    chunks = [_chunk(document.id, i) for i in range(3)]
    artifacts.write_chunks(document.id, chunks)
    service = _service(registry, artifacts, batch_size=10)

    messages = []
    service.ingest(document.id, progress=messages.append)

    assert any("embedding batch" in m.lower() for m in messages)
    assert any("stored 3/3" in m.lower() for m in messages)
    assert any("completed" in m.lower() for m in messages)


def test_ingest_is_idempotent_when_already_fully_embedded(artifacts):
    registry = InMemoryDocumentRegistry()
    document = _document()
    registry.register(document)
    chunks = [_chunk(document.id, i) for i in range(3)]
    artifacts.write_chunks(document.id, chunks)
    provider = FakeEmbeddingProvider()
    vector_store = FakeVectorStore()
    service = _service(registry, artifacts, provider=provider, vector_store=vector_store)

    first = service.ingest(document.id)
    second = service.ingest(document.id)

    assert first.skipped is False
    assert second.skipped is True
    # embed_batch was only ever called for the first run
    assert len(provider.calls) == 2  # batch_size=2 over 3 chunks -> 2 calls, first run only


def test_force_re_embeds_even_when_already_complete(artifacts):
    registry = InMemoryDocumentRegistry()
    document = _document()
    registry.register(document)
    chunks = [_chunk(document.id, i) for i in range(3)]
    artifacts.write_chunks(document.id, chunks)
    vector_store = FakeVectorStore()
    service = _service(registry, artifacts, vector_store=vector_store)

    service.ingest(document.id)
    result = service.ingest(document.id, force=True)

    assert result.skipped is False
    assert result.status == DocumentStatus.COMPLETED
    assert vector_store.deleted_documents == [document.id]


def test_partial_prior_run_is_cleared_and_retried(artifacts):
    registry = InMemoryDocumentRegistry()
    document = _document()
    registry.register(document)
    chunks = [_chunk(document.id, i) for i in range(4)]
    artifacts.write_chunks(document.id, chunks)
    vector_store = FakeVectorStore()
    # simulate an incomplete prior run: only 2 of 4 chunks' vectors present
    vector_store.upsert_raw(
        [
            (str(chunks[0].metadata.chunk_id), [1.0], {"document_id": str(document.id)}),
            (str(chunks[1].metadata.chunk_id), [1.0], {"document_id": str(document.id)}),
        ]
    )
    service = _service(registry, artifacts, vector_store=vector_store)

    result = service.ingest(document.id)

    assert result.status == DocumentStatus.COMPLETED
    assert result.chunks_embedded == 4
    assert vector_store.deleted_documents == [document.id]


def test_embedding_failure_marks_document_failed(artifacts):
    registry = InMemoryDocumentRegistry()
    document = _document()
    registry.register(document)
    chunks = [_chunk(document.id, i) for i in range(2)]
    artifacts.write_chunks(document.id, chunks)
    # fail every attempt (more than max_retries) so the batch ultimately raises
    provider = FakeEmbeddingProvider(fail_times=99)
    service = TextbookEmbeddingIngestionService(
        registry=registry,
        artifact_reader=artifacts,
        embedding_provider=provider,
        vector_store=FakeVectorStore(),
        embedding_batch_size=10,
        max_retries=1,
    )

    result = service.ingest(document.id)

    assert result.status == DocumentStatus.FAILED
    assert result.error is not None
    assert registry.get(document.id).status == DocumentStatus.FAILED


def test_transient_failure_is_retried_and_succeeds(artifacts):
    registry = InMemoryDocumentRegistry()
    document = _document()
    registry.register(document)
    chunks = [_chunk(document.id, i) for i in range(2)]
    artifacts.write_chunks(document.id, chunks)
    provider = FakeEmbeddingProvider(fail_times=1)  # fails once, then succeeds

    import app.ingestion.textbook.embedding_ingestion as module

    original_sleep = module.time.sleep
    module.time.sleep = lambda _seconds: None
    try:
        service = TextbookEmbeddingIngestionService(
            registry=registry,
            artifact_reader=artifacts,
            embedding_provider=provider,
            vector_store=FakeVectorStore(),
            embedding_batch_size=10,
            max_retries=3,
        )
        result = service.ingest(document.id)
    finally:
        module.time.sleep = original_sleep

    assert result.status == DocumentStatus.COMPLETED


def test_ingest_raises_for_unregistered_document(artifacts):
    registry = InMemoryDocumentRegistry()
    service = _service(registry, artifacts)

    with pytest.raises(IngestionError):
        service.ingest(uuid4())


def test_ingest_raises_when_chunks_artifact_missing(artifacts):
    registry = InMemoryDocumentRegistry()
    document = _document()
    registry.register(document)
    service = _service(registry, artifacts)

    with pytest.raises(IngestionError):
        service.ingest(document.id)


def test_payload_includes_required_textbook_metadata(artifacts):
    registry = InMemoryDocumentRegistry()
    document = _document()
    registry.register(document)
    chunks = [_chunk(document.id, 0)]
    artifacts.write_chunks(document.id, chunks)
    vector_store = FakeVectorStore()
    service = _service(registry, artifacts, vector_store=vector_store, batch_size=10)

    service.ingest(document.id)

    _, payload = next(iter(vector_store.points.values()))
    assert payload["document_id"] == str(document.id)
    assert payload["document_checksum"] == document.checksum
    assert payload["subject"] == "PHYSIOLOGY"
    assert payload["chapter_number"] == "9"
    assert payload["pdf_page_start"] == 117
    assert payload["text"] == "The cardiac cycle..."
