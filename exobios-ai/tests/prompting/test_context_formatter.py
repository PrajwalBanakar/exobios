from unittest.mock import patch

import pytest

from app.prompting.exceptions import ContextFormattingError
from app.prompting.formatting.context_formatter import ContextFormatter
from tests.retrieval.conftest import make_retrieved_chunk


def test_deduplicates_keeping_highest_score():
    chunk = make_retrieved_chunk(score=0.3)
    duplicate = make_retrieved_chunk(
        score=0.9, document_id=chunk.document_id, chunk_id=chunk.chunk_id
    )
    formatter = ContextFormatter()

    result = formatter.format([chunk, duplicate])

    assert result.total_chunks == 1
    kept = result.groups[0].citations[0]
    assert kept.chunk.score == 0.9


def test_sorts_by_score_descending():
    low = make_retrieved_chunk(score=0.1)
    high = make_retrieved_chunk(score=0.9)
    mid = make_retrieved_chunk(score=0.5)
    formatter = ContextFormatter()

    result = formatter.format([low, high, mid])

    flat = [c for g in result.groups for c in g.citations]
    assert [c.chunk.score for c in flat] == [0.9, 0.5, 0.1]


def test_deterministic_tiebreak_when_scores_are_equal():
    a = make_retrieved_chunk(score=0.5, filename="a.pdf")
    b = make_retrieved_chunk(score=0.5, filename="b.pdf")
    formatter = ContextFormatter()

    first_run = formatter.format([b, a])
    second_run = formatter.format([a, b])

    first_filenames = [c.chunk.filename for g in first_run.groups for c in g.citations]
    second_filenames = [c.chunk.filename for g in second_run.groups for c in g.citations]
    assert first_filenames == second_filenames == ["a.pdf", "b.pdf"]


def test_assigns_sequential_citation_numbers_in_relevance_order():
    high = make_retrieved_chunk(score=0.9)
    low = make_retrieved_chunk(score=0.2)
    formatter = ContextFormatter()

    result = formatter.format([low, high])

    flat = [c for g in result.groups for c in g.citations]
    assert [c.citation_number for c in flat] == [1, 2]
    assert flat[0].chunk.score == 0.9


def test_groups_by_document_preserving_relevance_order_of_first_appearance():
    doc_a_chunk_1 = make_retrieved_chunk(score=0.9)
    doc_b_chunk = make_retrieved_chunk(score=0.8)
    doc_a_chunk_2 = make_retrieved_chunk(
        score=0.1,
        document_id=doc_a_chunk_1.document_id,
        filename=doc_a_chunk_1.filename,
        document_type=doc_a_chunk_1.document_type,
        source=doc_a_chunk_1.source,
    )
    formatter = ContextFormatter()

    result = formatter.format([doc_a_chunk_2, doc_b_chunk, doc_a_chunk_1])

    assert len(result.groups) == 2
    assert result.groups[0].document_id == doc_a_chunk_1.document_id
    assert [c.chunk.score for c in result.groups[0].citations] == [0.9, 0.1]
    assert result.groups[1].document_id == doc_b_chunk.document_id


def test_preserves_source_attribution_in_groups():
    chunk = make_retrieved_chunk(filename="clinical_guide.pdf", source="who-guidelines")
    formatter = ContextFormatter()

    result = formatter.format([chunk])

    group = result.groups[0]
    assert group.filename == "clinical_guide.pdf"
    assert group.source == "who-guidelines"
    assert group.document_type == chunk.document_type


def test_empty_input_returns_empty_groups():
    formatter = ContextFormatter()

    result = formatter.format([])

    assert result.groups == []
    assert result.total_chunks == 0


def test_wraps_unexpected_exception_as_context_formatting_error():
    formatter = ContextFormatter()
    with patch.object(formatter, "_sort_deterministically", side_effect=RuntimeError("boom")):
        with pytest.raises(ContextFormattingError):
            formatter.format([make_retrieved_chunk()])
