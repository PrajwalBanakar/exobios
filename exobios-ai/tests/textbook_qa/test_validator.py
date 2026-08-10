import pytest

from app.prompting.formatting.context_formatter import ContextFormatter
from app.textbook_qa.exceptions import TextbookAnswerValidationError
from app.textbook_qa.models import TextbookAnswerDraft
from app.textbook_qa.validator import TextbookAnswerValidator


def _context(chunks):
    return ContextFormatter().format(chunks)


def test_valid_citation_resolves_to_trusted_metadata(textbook_chunk_factory):
    chunk = textbook_chunk_factory()
    context = _context([chunk])
    draft = TextbookAnswerDraft(
        insufficient_evidence=False, answer="The cycle has two phases [S1].", citations=[1]
    )

    resolved = TextbookAnswerValidator().validate_and_resolve(draft, context)

    assert len(resolved) == 1
    assert resolved[0].citation_number == 1
    assert resolved[0].document_id == chunk.document_id
    assert resolved[0].chapter_number == "9"
    assert resolved[0].pdf_page_start == 117


def test_unknown_citation_number_is_rejected(textbook_chunk_factory):
    chunk = textbook_chunk_factory()
    context = _context([chunk])
    draft = TextbookAnswerDraft(insufficient_evidence=False, answer="Answer [S99].", citations=[99])

    with pytest.raises(TextbookAnswerValidationError):
        TextbookAnswerValidator().validate_and_resolve(draft, context)


def test_answer_with_zero_citations_is_rejected(textbook_chunk_factory):
    chunk = textbook_chunk_factory()
    context = _context([chunk])
    draft = TextbookAnswerDraft(
        insufficient_evidence=False, answer="An ungrounded answer.", citations=[]
    )

    with pytest.raises(TextbookAnswerValidationError):
        TextbookAnswerValidator().validate_and_resolve(draft, context)


def test_blank_answer_is_rejected(textbook_chunk_factory):
    chunk = textbook_chunk_factory()
    context = _context([chunk])
    # citations=[1] with a blank answer is malformed regardless
    draft = TextbookAnswerDraft.model_construct(
        insufficient_evidence=False, answer="   ", citations=[1]
    )

    with pytest.raises(TextbookAnswerValidationError):
        TextbookAnswerValidator().validate_and_resolve(draft, context)


def test_duplicate_citation_numbers_resolved_once(textbook_chunk_factory):
    chunk = textbook_chunk_factory()
    context = _context([chunk])
    draft = TextbookAnswerDraft(
        insufficient_evidence=False, answer="Answer [S1] [S1].", citations=[1, 1]
    )

    resolved = TextbookAnswerValidator().validate_and_resolve(draft, context)

    assert len(resolved) == 1


def test_multiple_valid_citations_all_resolve(textbook_chunk_factory):
    chunks = [textbook_chunk_factory(score=0.9), textbook_chunk_factory(score=0.8)]
    context = _context(chunks)
    draft = TextbookAnswerDraft(
        insufficient_evidence=False, answer="Answer [S1] and [S2].", citations=[1, 2]
    )

    resolved = TextbookAnswerValidator().validate_and_resolve(draft, context)

    assert {c.citation_number for c in resolved} == {1, 2}
