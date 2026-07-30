import pytest
from qdrant_client import models

from app.embeddings.exceptions import VectorStoreError
from app.embeddings.models.embedding import EmbeddedChunk, EmbeddingVector
from app.embeddings.vectorstores.qdrant_store import QdrantVectorStore
from tests.embeddings.conftest import make_chunk, make_document_metadata


def _store(fake_qdrant_client, **kwargs) -> QdrantVectorStore:
    defaults = {"client": fake_qdrant_client, "collection_name": "exobios_chunks", "vector_size": 8}
    defaults.update(kwargs)
    return QdrantVectorStore(**defaults)


def test_initialize_creates_collection_when_missing(fake_qdrant_client):
    store = _store(fake_qdrant_client)

    store.initialize()

    assert len(fake_qdrant_client.created_collections) == 1
    name, vectors_config = fake_qdrant_client.created_collections[0]
    assert name == "exobios_chunks"
    assert vectors_config.size == 8
    assert vectors_config.distance == models.Distance.COSINE


def test_initialize_is_idempotent_when_collection_already_exists(fake_qdrant_client):
    fake_qdrant_client._collections.add("exobios_chunks")
    store = _store(fake_qdrant_client)

    store.initialize()

    assert fake_qdrant_client.created_collections == []


def test_initialize_wraps_client_errors_in_vector_store_error(fake_qdrant_client):
    fake_qdrant_client.fail_with = RuntimeError("connection refused")
    store = _store(fake_qdrant_client)

    with pytest.raises(VectorStoreError):
        store.initialize()


def test_upsert_chunks_sends_correct_payload(fake_qdrant_client):
    store = _store(fake_qdrant_client)
    document = make_document_metadata(
        filename="report.pdf",
        tags=["intake", "cardiology"],
        language="en",
        version="2.0",
        source="clinic-a",
    )
    chunk = make_chunk(
        document.id, chunk_number=1, text="patient history", section_title="History"
    )
    vector = EmbeddingVector(values=[0.1, 0.2], model="m", dimensions=2)
    embedded = [EmbeddedChunk(chunk=chunk, vector=vector)]

    store.upsert_chunks(document, embedded)

    assert len(fake_qdrant_client.upserted) == 1
    collection_name, points = fake_qdrant_client.upserted[0]
    assert collection_name == "exobios_chunks"
    assert len(points) == 1
    point = points[0]
    assert point.id == str(chunk.id)
    assert point.vector == [0.1, 0.2]
    assert point.payload == {
        "document_id": str(document.id),
        "chunk_id": str(chunk.id),
        "page_number": chunk.metadata.page_number,
        "start_offset": chunk.metadata.start_offset,
        "end_offset": chunk.metadata.end_offset,
        "section_title": "History",
        "document_type": "TXT",
        "filename": "report.pdf",
        "language": "en",
        "tags": ["intake", "cardiology"],
        "version": "2.0",
        "source": "clinic-a",
    }


def test_upsert_chunks_skips_client_call_for_empty_list(fake_qdrant_client):
    store = _store(fake_qdrant_client)
    document = make_document_metadata()

    store.upsert_chunks(document, [])

    assert fake_qdrant_client.upserted == []


def test_upsert_chunks_wraps_client_errors(fake_qdrant_client):
    fake_qdrant_client.fail_with = RuntimeError("timeout")
    store = _store(fake_qdrant_client)
    document = make_document_metadata()
    chunk = make_chunk(document.id)
    vector = EmbeddingVector(values=[0.1], model="m", dimensions=1)
    embedded = [EmbeddedChunk(chunk=chunk, vector=vector)]

    with pytest.raises(VectorStoreError):
        store.upsert_chunks(document, embedded)


def test_delete_document_filters_by_document_id(fake_qdrant_client):
    store = _store(fake_qdrant_client)
    document_id = make_document_metadata().id

    store.delete_document(document_id)

    assert len(fake_qdrant_client.deleted) == 1
    collection_name, points_selector = fake_qdrant_client.deleted[0]
    assert collection_name == "exobios_chunks"
    condition = points_selector.filter.must[0]
    assert condition.key == "document_id"
    assert condition.match.value == str(document_id)


def test_document_exists_true_when_points_are_found(fake_qdrant_client):
    fake_qdrant_client.scroll_result = ([object()], None)
    store = _store(fake_qdrant_client)

    assert store.document_exists(make_document_metadata().id) is True


def test_document_exists_false_when_no_points_are_found(fake_qdrant_client):
    fake_qdrant_client.scroll_result = ([], None)
    store = _store(fake_qdrant_client)

    assert store.document_exists(make_document_metadata().id) is False


def test_document_exists_wraps_client_errors(fake_qdrant_client):
    fake_qdrant_client.fail_with = RuntimeError("boom")
    store = _store(fake_qdrant_client)

    with pytest.raises(VectorStoreError):
        store.document_exists(make_document_metadata().id)


def test_health_returns_true_when_client_reachable(fake_qdrant_client):
    store = _store(fake_qdrant_client)

    assert store.health() is True


def test_health_returns_false_when_client_unreachable(fake_qdrant_client):
    fake_qdrant_client.fail_with = RuntimeError("unreachable")
    store = _store(fake_qdrant_client)

    assert store.health() is False
