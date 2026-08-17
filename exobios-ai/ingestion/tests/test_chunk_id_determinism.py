from types import SimpleNamespace

import pytest

pytest.importorskip("docling", reason="chunker module pulls in docling's HybridChunker + tiktoken at import time")

from chunkers.chunker import _build_chunk_metadata  # noqa: E402


def _fake_docling_chunk(text: str = "some chunk text", page_no: int = 3):
    prov = SimpleNamespace(page_no=page_no)
    doc_item = SimpleNamespace(prov=[prov])
    meta = SimpleNamespace(headings=["Section", "Subsection"], doc_items=[doc_item])
    return SimpleNamespace(text=text, meta=meta)


def test_same_document_and_position_yields_same_chunk_id():
    chunk = _fake_docling_chunk()
    first = _build_chunk_metadata(chunk, document_id="doc-123", index=0)
    second = _build_chunk_metadata(chunk, document_id="doc-123", index=0)
    assert first.chunk_id == second.chunk_id


def test_different_position_yields_different_chunk_id():
    chunk = _fake_docling_chunk()
    first = _build_chunk_metadata(chunk, document_id="doc-123", index=0)
    second = _build_chunk_metadata(chunk, document_id="doc-123", index=1)
    assert first.chunk_id != second.chunk_id


def test_different_document_yields_different_chunk_id_for_same_position():
    chunk = _fake_docling_chunk()
    first = _build_chunk_metadata(chunk, document_id="doc-123", index=0)
    second = _build_chunk_metadata(chunk, document_id="doc-456", index=0)
    assert first.chunk_id != second.chunk_id
