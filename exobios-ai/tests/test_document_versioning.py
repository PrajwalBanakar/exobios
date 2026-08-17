"""Tests for the retrieval-side half of the document-versioning foundation:
QdrantService._build_filter always excludes chunks explicitly marked
document_payload.is_active == false, while never excluding chunks that
simply don't have the field at all (the entire pre-versioning corpus). See
the 2026-08 audit's Priority 8 and ingestion/services/upload.py for the
ingestion-side supersession logic."""

from qdrant_client import models

from services.qdrant_service import QdrantService


def test_filter_always_excludes_explicitly_inactive_documents():
    qdrant_filter = QdrantService._build_filter({})

    assert qdrant_filter.must_not == [
        models.FieldCondition(key="document_payload.is_active", match=models.MatchValue(value=False))
    ]


def test_filter_combines_category_filter_with_active_exclusion():
    qdrant_filter = QdrantService._build_filter({"complaint_category": "FEVER"})

    assert qdrant_filter.must == [
        models.FieldCondition(key="document_payload.complaint_category", match=models.MatchValue(value="FEVER"))
    ]
    assert qdrant_filter.must_not == [
        models.FieldCondition(key="document_payload.is_active", match=models.MatchValue(value=False))
    ]


def test_filter_is_never_none_even_with_no_category_filters():
    # Previously _build_filter returned None for an empty filters dict,
    # meaning no filter at all was applied. It must now always at least
    # carry the is_active exclusion.
    qdrant_filter = QdrantService._build_filter(None)
    assert qdrant_filter is not None
    assert qdrant_filter.must_not
