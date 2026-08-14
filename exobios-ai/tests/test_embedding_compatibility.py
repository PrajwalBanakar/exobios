"""Tests for services/qdrant_service.py's embedding compatibility guard —
detects "ingestion embedding model != query embedding model" and "expected
dimension != Qdrant vector dimension" using the sentinel metadata point
ingestion/store/qdrant_store.py writes into each collection."""

import pytest

from config.settings import settings
from core.exceptions import EmbeddingCompatibilityError
from services.qdrant_service import QdrantService, _CORPUS_METADATA_POINT_ID


class _Point:
    def __init__(self, payload):
        self.payload = payload


class _FakeClient:
    def __init__(self, retrieve_result):
        self._retrieve_result = retrieve_result

    def retrieve(self, collection_name, ids, with_payload=True):
        assert ids == [_CORPUS_METADATA_POINT_ID]
        return self._retrieve_result

    def get_collections(self):
        # /health/ready's separate Qdrant-reachability check calls this —
        # tests in this file that go through the HTTP endpoint need it too.
        return object()


def _service_with(retrieve_result) -> QdrantService:
    service = QdrantService.__new__(QdrantService)  # skip __init__'s real client/sparse model construction
    service.client = _FakeClient(retrieve_result)
    service.collection_name = settings.qdrant.collection_name
    service._compatibility_checked = False
    service.compatibility_warning = None
    return service


def test_matching_metadata_passes_silently():
    service = _service_with([_Point({
        "embedding_model": settings.embedding.embed_model,
        "embedding_dimension": settings.embedding.vector_size,
    })])
    service.verify_embedding_compatibility()  # must not raise
    assert service.compatibility_warning is None


def test_mismatched_model_raises():
    service = _service_with([_Point({
        "embedding_model": "some-other-model",
        "embedding_dimension": settings.embedding.vector_size,
    })])
    with pytest.raises(EmbeddingCompatibilityError) as exc_info:
        service.verify_embedding_compatibility()
    assert "some-other-model" in exc_info.value.message


def test_mismatched_dimension_raises():
    service = _service_with([_Point({
        "embedding_model": settings.embedding.embed_model,
        "embedding_dimension": 1536,
    })])
    with pytest.raises(EmbeddingCompatibilityError) as exc_info:
        service.verify_embedding_compatibility()
    assert "1536" in exc_info.value.message


def test_missing_metadata_is_non_fatal_warning_only():
    service = _service_with([])  # legacy corpus, ingested before this guard existed
    service.verify_embedding_compatibility()  # must not raise
    assert service.compatibility_warning is not None
    assert "no compatibility metadata" in service.compatibility_warning


def test_result_is_cached_after_first_call():
    service = _service_with([_Point({
        "embedding_model": settings.embedding.embed_model,
        "embedding_dimension": settings.embedding.vector_size,
    })])
    service.verify_embedding_compatibility()
    # Swap in a client that would raise if called again — proves caching.
    service.client = _FakeClient(None)

    def _boom(*a, **k):
        raise AssertionError("should not re-query once cached")
    service.client.retrieve = _boom
    service.verify_embedding_compatibility()  # cached — must not touch client again


def test_health_ready_reports_ok_when_metadata_matches(client, monkeypatch):
    from services import qdrant_service as qdrant_module

    monkeypatch.setattr(qdrant_module.qdrant_service, "_compatibility_checked", False)
    monkeypatch.setattr(qdrant_module.qdrant_service, "client", _FakeClient([_Point({
        "embedding_model": settings.embedding.embed_model,
        "embedding_dimension": settings.embedding.vector_size,
    })]))

    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["checks"]["embedding_compatibility"] == "ok"


def test_health_ready_returns_503_on_confirmed_mismatch(client, monkeypatch):
    from services import qdrant_service as qdrant_module

    monkeypatch.setattr(qdrant_module.qdrant_service, "_compatibility_checked", False)
    monkeypatch.setattr(qdrant_module.qdrant_service, "client", _FakeClient([_Point({
        "embedding_model": "wrong-model",
        "embedding_dimension": settings.embedding.vector_size,
    })]))

    response = client.get("/health/ready")
    assert response.status_code == 503
    assert "mismatch" in response.json()["checks"]["embedding_compatibility"]


def test_health_ready_does_not_gate_on_missing_metadata(client, monkeypatch):
    from services import qdrant_service as qdrant_module

    monkeypatch.setattr(qdrant_module.qdrant_service, "_compatibility_checked", False)
    monkeypatch.setattr(qdrant_module.qdrant_service, "client", _FakeClient([]))

    response = client.get("/health/ready")
    assert response.status_code == 200
    assert "no compatibility metadata" in response.json()["checks"]["embedding_compatibility"]
