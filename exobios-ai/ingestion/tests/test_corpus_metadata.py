"""ingestion/store/qdrant_store.py writes a sentinel point per collection
recording which embedding model/dimension it was ingested with —
app/services/qdrant_service.py reads this to detect config drift before
trusting retrieval. See the 2026-08 audit's Priority 6."""

import pytest

pytest.importorskip("qdrant_client", reason="qdrant_store pulls in qdrant_client + fastembed at import time")

import store.qdrant_store as qdrant_store  # noqa: E402
from qdrant_client import models  # noqa: E402
from embedder.embedder import EMBED_MODEL_NAME  # noqa: E402


def test_write_corpus_metadata_uses_the_documented_sentinel_id(monkeypatch):
    captured = {}

    def _fake_upsert(collection_name, points):
        captured["collection_name"] = collection_name
        captured["points"] = points

    monkeypatch.setattr(qdrant_store, "_client", type("C", (), {"upsert": staticmethod(_fake_upsert)})())
    monkeypatch.setattr(qdrant_store, "_get_sparse_vector", lambda text: models.SparseVector(indices=[0], values=[1.0]))

    qdrant_store._write_corpus_metadata()

    assert len(captured["points"]) == 1
    point = captured["points"][0]
    assert str(point.id) == qdrant_store.CORPUS_METADATA_POINT_ID


def test_write_corpus_metadata_payload_matches_actual_embedding_config(monkeypatch):
    captured = {}

    def _fake_upsert(collection_name, points):
        captured["points"] = points

    monkeypatch.setattr(qdrant_store, "_client", type("C", (), {"upsert": staticmethod(_fake_upsert)})())
    monkeypatch.setattr(qdrant_store, "_get_sparse_vector", lambda text: models.SparseVector(indices=[0], values=[1.0]))

    qdrant_store._write_corpus_metadata()

    payload = captured["points"][0].payload
    assert payload["embedding_model"] == EMBED_MODEL_NAME
    assert payload["embedding_dimension"] == qdrant_store.VECTOR_SIZE
    assert payload["_is_corpus_metadata"] is True


def test_write_corpus_metadata_dense_vector_matches_configured_dimension(monkeypatch):
    captured = {}

    def _fake_upsert(collection_name, points):
        captured["points"] = points

    monkeypatch.setattr(qdrant_store, "_client", type("C", (), {"upsert": staticmethod(_fake_upsert)})())
    monkeypatch.setattr(qdrant_store, "_get_sparse_vector", lambda text: models.SparseVector(indices=[0], values=[1.0]))

    qdrant_store._write_corpus_metadata()

    dense_vector = captured["points"][0].vector["dense"]
    assert len(dense_vector) == qdrant_store.VECTOR_SIZE
