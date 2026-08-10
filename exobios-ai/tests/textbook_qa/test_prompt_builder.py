import pytest

from app.prompting.formatting.context_formatter import ContextFormatter
from app.textbook_qa.exceptions import UnsupportedGroundingModeError
from app.textbook_qa.models import GroundingMode
from app.textbook_qa.prompt_builder import TextbookPromptBuilder


def _builder() -> TextbookPromptBuilder:
    return TextbookPromptBuilder(context_formatter=ContextFormatter())


def test_build_includes_question_and_evidence(textbook_chunk_factory):
    chunk = textbook_chunk_factory(text="The cardiac cycle has two phases.")

    prompt, context = _builder().build("Explain the cardiac cycle", [chunk], GroundingMode.STRICT)

    assert "Explain the cardiac cycle" in prompt
    assert "The cardiac cycle has two phases." in prompt
    assert context.total_chunks == 1


def test_build_numbers_citations_with_s_prefix(textbook_chunk_factory):
    chunks = [textbook_chunk_factory(score=0.9), textbook_chunk_factory(score=0.8)]

    prompt, _ = _builder().build("q", chunks, GroundingMode.STRICT)

    assert "[S1]" in prompt
    assert "[S2]" in prompt


def test_build_includes_strict_grounding_instructions(textbook_chunk_factory):
    chunk = textbook_chunk_factory()

    prompt, _ = _builder().build("q", [chunk], GroundingMode.STRICT)

    assert "insufficient_evidence" in prompt
    assert "ONLY" in prompt
    assert "never invent" in prompt.lower()


def test_build_handles_no_retrieved_chunks():
    prompt, context = _builder().build("q", [], GroundingMode.STRICT)

    assert "No relevant textbook evidence was retrieved." in prompt
    assert context.total_chunks == 0


def test_build_raises_for_unsupported_grounding_mode(textbook_chunk_factory):
    chunk = textbook_chunk_factory()

    with pytest.raises(UnsupportedGroundingModeError):
        _builder().build("q", [chunk], GroundingMode.AUGMENTED)

    with pytest.raises(UnsupportedGroundingModeError):
        _builder().build("q", [chunk], GroundingMode.GENERAL)
