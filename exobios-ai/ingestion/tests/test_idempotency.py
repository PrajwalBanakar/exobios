"""Idempotency is the core production-readiness gap this pipeline had: doc_id
and chunk_id used to be fresh uuid4()s on every run, so any crash/retry or
deliberate re-run duplicated a document's rows/vectors instead of updating
them in place. Both ids are now derived deterministically (see
loaders/loader.py::_compute_document_id and chunkers/chunker.py's
_CHUNK_ID_NAMESPACE) — these tests pin that property down directly, without
exercising the full pipeline (which needs live Qdrant/Supabase/HF network
access and is out of scope for a unit test)."""

import hashlib
import uuid

import pytest

pytest.importorskip("docling", reason="ingestion's loader module pulls in the full docling/fastembed import chain")

from loaders.loader import _compute_document_id, _DOCUMENT_ID_NAMESPACE  # noqa: E402


def test_same_file_content_produces_same_document_id(tmp_path):
    file_a = tmp_path / "a.pdf"
    file_a.write_bytes(b"identical content")
    file_b = tmp_path / "differently-named.pdf"
    file_b.write_bytes(b"identical content")

    doc_id_a, hash_a = _compute_document_id(file_a)
    doc_id_b, hash_b = _compute_document_id(file_b)

    assert doc_id_a == doc_id_b
    assert hash_a == hash_b


def test_different_file_content_produces_different_document_id(tmp_path):
    file_a = tmp_path / "a.pdf"
    file_a.write_bytes(b"version one")
    doc_id_a, _ = _compute_document_id(file_a)

    # Same path, overwritten with different content — simulates "the file at
    # this location changed" (a real re-ingestion-after-edit scenario).
    file_a.write_bytes(b"version two")
    doc_id_b, _ = _compute_document_id(file_a)

    assert doc_id_a != doc_id_b


def test_document_id_matches_expected_derivation(tmp_path):
    content = b"some pdf bytes"
    f = tmp_path / "doc.pdf"
    f.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()
    expected_id = str(uuid.uuid5(_DOCUMENT_ID_NAMESPACE, expected_hash))

    doc_id, content_hash = _compute_document_id(f)

    assert content_hash == expected_hash
    assert doc_id == expected_id


def test_rerunning_ingestion_on_same_file_is_idempotent_at_the_id_level(tmp_path):
    """Simulates "crash and retry" / "deliberate re-run": computing the id
    twice for the same file must be stable, since that stability is what
    makes the Supabase upsert and Qdrant point-id upsert overwrite in place
    instead of duplicating."""
    f = tmp_path / "textbook.pdf"
    f.write_bytes(b"a whole textbook's worth of bytes" * 1000)

    first_run = _compute_document_id(f)
    second_run = _compute_document_id(f)

    assert first_run == second_run
