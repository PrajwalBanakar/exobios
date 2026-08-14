"""Unit tests for services/reranker_service.py's actual reordering logic —
tests/conftest.py's autouse fixture mocks this service as an identity
function for the rest of the suite, so these tests exercise the real
implementation directly instead.

As of the 2026-08 audit, no cross-encoder/text-ranking model has an active
hosted-inference provider on HF's router (verified live — see
docs/ARCHITECTURE.md's Reranker section), so there is no live model to test
against. These tests instead prove the service-layer mechanism itself is
correct: given a well-formed scoring response, candidates ARE reordered by
score; given a failure or a disabled config, the original retrieval-fusion
order is preserved rather than the request failing.
"""

import requests

from config.settings import settings
from services.reranker_service import RerankerService


def _candidates():
    return [
        {"chunk_id": "a", "text": "irrelevant text about cars"},
        {"chunk_id": "b", "text": "highly relevant text about dengue fever"},
        {"chunk_id": "c", "text": "somewhat relevant text about fever"},
    ]


def test_rerank_reorders_candidates_by_score(monkeypatch):
    service = RerankerService()
    monkeypatch.setattr(settings.reranker, "enabled", True)

    class _Resp:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            # scores intentionally out of input order — b highest, then c, then a
            return [0.1, 0.9, 0.5]

    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp())

    result = service.rerank("dengue fever query", _candidates(), top_k=3)

    assert [c["chunk_id"] for c in result] == ["b", "c", "a"]


def test_rerank_respects_top_k_after_reordering(monkeypatch):
    service = RerankerService()
    monkeypatch.setattr(settings.reranker, "enabled", True)

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return [0.1, 0.9, 0.5]

    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp())

    result = service.rerank("query", _candidates(), top_k=2)

    assert [c["chunk_id"] for c in result] == ["b", "c"]


def test_rerank_falls_back_to_original_order_on_http_failure(monkeypatch):
    service = RerankerService()
    monkeypatch.setattr(settings.reranker, "enabled", True)

    def _boom(*a, **k):
        raise requests.exceptions.ConnectionError("HF unreachable")

    monkeypatch.setattr(requests, "post", _boom)

    result = service.rerank("query", _candidates(), top_k=3)

    assert [c["chunk_id"] for c in result] == ["a", "b", "c"]


def test_rerank_falls_back_on_malformed_response_shape(monkeypatch):
    service = RerankerService()
    monkeypatch.setattr(settings.reranker, "enabled", True)

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"unexpected": "shape"}

    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp())

    result = service.rerank("query", _candidates(), top_k=3)

    assert [c["chunk_id"] for c in result] == ["a", "b", "c"]


def test_rerank_skips_http_call_entirely_when_disabled(monkeypatch):
    service = RerankerService()
    monkeypatch.setattr(settings.reranker, "enabled", False)

    def _should_not_be_called(*a, **k):
        raise AssertionError("HTTP call must not happen when reranker is disabled")

    monkeypatch.setattr(requests, "post", _should_not_be_called)

    result = service.rerank("query", _candidates(), top_k=3)

    assert [c["chunk_id"] for c in result] == ["a", "b", "c"]


def test_rerank_empty_candidates_short_circuits(monkeypatch):
    service = RerankerService()
    monkeypatch.setattr(settings.reranker, "enabled", True)

    def _should_not_be_called(*a, **k):
        raise AssertionError("HTTP call must not happen for empty candidates")

    monkeypatch.setattr(requests, "post", _should_not_be_called)

    assert service.rerank("query", [], top_k=3) == []
