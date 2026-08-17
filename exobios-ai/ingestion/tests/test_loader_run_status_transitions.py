"""Integration-style tests for loaders/loader.py::run()'s status-lifecycle
wiring — proves COMPLETED/FAILED are actually set at the right points, not
just that update_document_status works in isolation (see
test_ingestion_status.py for that). Every external call (Docling, HF
classification, HF embedding, Qdrant, Supabase) is mocked; only the
orchestration logic in run() itself is exercised."""

from types import SimpleNamespace

import pytest

pytest.importorskip("docling", reason="loader pulls in the full docling/fastembed import chain")

import loaders.loader as loader_module  # noqa: E402
from schemas.document_schema import DocumentStatus  # noqa: E402


def _fake_docling_document():
    return SimpleNamespace(pages=[1, 2, 3], export_to_markdown=lambda: "# doc")


def _fake_classified():
    return {"title": "Test Doc", "category_scores": {"FEVER": 0.9}, "role_scores": {"ASHA": 0.8}}


@pytest.fixture
def wired(monkeypatch, tmp_path):
    """Mocks every external call in the pipeline and returns a recorder of
    update_document_status calls, keyed for assertions."""
    doc_file = tmp_path / "test.pdf"
    doc_file.write_bytes(b"fake pdf content")

    status_calls = []
    supersede_calls = []

    monkeypatch.setattr(loader_module, "load_documents", lambda folder: iter([doc_file]))
    monkeypatch.setattr(loader_module, "convert_to_docling_document", lambda path: _fake_docling_document())
    monkeypatch.setattr(loader_module, "classify", lambda doc: _fake_classified())
    monkeypatch.setattr(loader_module, "storeParsedDocLocally", lambda content, path: None)
    monkeypatch.setattr(loader_module, "save_document_metadata", lambda metadata: True)
    monkeypatch.setattr(
        loader_module, "update_document_status",
        lambda doc_id, status, error_message=None: status_calls.append((doc_id, status, error_message)),
    )
    # Simulates one prior active version existing for this logical document —
    # tests assert whether/when it gets superseded.
    monkeypatch.setattr(loader_module, "find_active_versions", lambda key, exclude_document_id: ["prior-version-doc-id"])
    monkeypatch.setattr(
        loader_module, "mark_superseded",
        lambda document_id, superseded_by: supersede_calls.append((document_id, superseded_by)),
    )
    return SimpleNamespace(status_calls=status_calls, supersede_calls=supersede_calls)


def test_successful_ingestion_ends_in_completed(monkeypatch, wired):
    monkeypatch.setattr(loader_module, "chunk_docling_document", lambda doc, doc_id: ["chunk1"])
    monkeypatch.setattr(loader_module, "embed_chunks", lambda chunks: ["vector1"])
    monkeypatch.setattr(loader_module, "build_metadata_payloads", lambda chunks, vectors, metadata: ["payload1"])
    monkeypatch.setattr(loader_module, "store_metadata_payloads", lambda payloads: True)

    loader_module.run()

    assert len(wired.status_calls) == 1
    doc_id, status, error_message = wired.status_calls[0]
    assert status == DocumentStatus.COMPLETED
    assert error_message is None

    # Only on success: the prior active version of this logical document is
    # superseded by the one that just completed.
    assert wired.supersede_calls == [("prior-version-doc-id", doc_id)]


def test_embedding_failure_ends_in_failed_with_reason(monkeypatch, wired):
    monkeypatch.setattr(loader_module, "chunk_docling_document", lambda doc, doc_id: ["chunk1"])

    def _boom(chunks):
        raise RuntimeError("embedding failed after 4 attempts")

    monkeypatch.setattr(loader_module, "embed_chunks", _boom)
    # build_metadata_payloads/store_metadata_payloads must not even be reached
    monkeypatch.setattr(loader_module, "build_metadata_payloads", lambda *a: (_ for _ in ()).throw(AssertionError("unreachable")))
    monkeypatch.setattr(loader_module, "store_metadata_payloads", lambda *a: (_ for _ in ()).throw(AssertionError("unreachable")))

    loader_module.run()

    assert len(wired.status_calls) == 1
    doc_id, status, error_message = wired.status_calls[0]
    assert status == DocumentStatus.FAILED
    assert "embedding failed" in error_message
    # A failed re-ingestion must never deactivate a working prior version.
    assert wired.supersede_calls == []


def test_qdrant_upsert_failure_ends_in_failed_and_is_resumable(monkeypatch, wired):
    monkeypatch.setattr(loader_module, "chunk_docling_document", lambda doc, doc_id: ["chunk1"])
    monkeypatch.setattr(loader_module, "embed_chunks", lambda chunks: ["vector1"])
    monkeypatch.setattr(loader_module, "build_metadata_payloads", lambda chunks, vectors, metadata: ["payload1"])
    monkeypatch.setattr(loader_module, "store_metadata_payloads", lambda payloads: False)  # Qdrant upsert failed

    loader_module.run()

    assert len(wired.status_calls) == 1
    doc_id, status, error_message = wired.status_calls[0]
    assert status == DocumentStatus.FAILED
    assert "qdrant" in error_message.lower() or "re-run" in error_message.lower()
    assert wired.supersede_calls == []


def test_metadata_save_failure_never_reaches_status_update(monkeypatch, wired):
    # If save_document_metadata itself fails, there's no row to update — the
    # loop must skip to the next file, not call update_document_status.
    monkeypatch.setattr(loader_module, "save_document_metadata", lambda metadata: False)
    monkeypatch.setattr(loader_module, "chunk_docling_document", lambda *a: (_ for _ in ()).throw(AssertionError("unreachable")))

    loader_module.run()

    assert wired.status_calls == []
