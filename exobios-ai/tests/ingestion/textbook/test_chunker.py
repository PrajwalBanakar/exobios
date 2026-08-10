from uuid import uuid4

import pytest

from app.ingestion.models.document import Subject
from app.ingestion.textbook.chunker import TextbookChunker
from app.ingestion.textbook.models import (
    ContentBlock,
    DetectedHeading,
    HeadingLevel,
    PageClassification,
)
from app.prompting.builders.rag_prompt_builder import count_tokens

_DOCUMENT_ID = uuid4()


def _chapter_block(number: str, title: str, page: int) -> ContentBlock:
    return ContentBlock(
        pdf_page_number=page,
        printed_page_number=page,
        text=f"CHAPTER {number} {title}",
        heading=DetectedHeading(level=HeadingLevel.CHAPTER, text=title, number=number),
        page_classification=PageClassification.MAIN_CONTENT,
    )


def _heading_block(text: str, page: int) -> ContentBlock:
    return ContentBlock(
        pdf_page_number=page,
        printed_page_number=page,
        text=text,
        heading=DetectedHeading(level=HeadingLevel.HEADING, text=text),
        page_classification=PageClassification.MAIN_CONTENT,
    )


def _body_block(
    text: str, page: int, *, is_table: bool = False, is_caption: bool = False
) -> ContentBlock:
    return ContentBlock(
        pdf_page_number=page,
        printed_page_number=page,
        text=text,
        heading=None,
        is_table=is_table,
        is_figure_caption=is_caption,
        page_classification=PageClassification.MAIN_CONTENT,
    )


def _sentence(n: int) -> str:
    return " ".join(f"Sentence number {i} about the cardiac cycle." for i in range(n))


def _chunker(target=50, max_tokens=100, overlap=10, min_useful=5) -> TextbookChunker:
    return TextbookChunker(
        target_tokens=target,
        max_tokens=max_tokens,
        overlap_tokens=overlap,
        min_useful_tokens=min_useful,
    )


def test_respects_target_token_budget_approximately():
    blocks = [
        _chapter_block("9", "Heart Muscle", 1),
        _heading_block("The Cardiac Cycle", 1),
        _body_block(_sentence(40), 1),
    ]
    chunker = _chunker(target=50, max_tokens=200)

    chunks = chunker.chunk(_DOCUMENT_ID, Subject.PHYSIOLOGY, "Physiology", "14th", blocks)

    # a long single body block after a small heading should get split near
    # target once the chapter's opening heading content is flushed. A small
    # margin above max_tokens is expected: the context prefix (Step 20) is
    # added after budgeting and reserves only a fixed headroom, not an exact
    # accounting of its own length.
    assert len(chunks) >= 1
    assert all(c.metadata.token_count <= 200 + 15 for c in chunks)


def test_never_exceeds_max_tokens_except_a_single_oversized_block():
    blocks = [
        _chapter_block("9", "Heart Muscle", 1),
        _body_block(_sentence(10), 1),
        _body_block(_sentence(10), 1),
        _body_block(_sentence(10), 1),
    ]
    chunker = _chunker(target=30, max_tokens=60)

    chunks = chunker.chunk(_DOCUMENT_ID, Subject.PHYSIOLOGY, "Physiology", "14th", blocks)

    assert all(c.metadata.token_count <= 60 for c in chunks)


def test_oversized_single_block_is_split_via_sentences_not_dropped():
    huge_block = _body_block(_sentence(200), 1)
    blocks = [_chapter_block("9", "Heart Muscle", 1), huge_block]
    chunker = _chunker(target=50, max_tokens=80)

    chunks = chunker.chunk(_DOCUMENT_ID, Subject.PHYSIOLOGY, "Physiology", "14th", blocks)

    assert len(chunks) > 1
    # every emitted chunk still respects (or is close to) the ceiling
    assert all(c.metadata.token_count <= 90 for c in chunks)
    # no content lost: every sentence marker should appear somewhere
    combined = " ".join(c.text for c in chunks)
    assert "Sentence number 0" in combined
    assert "Sentence number 199" in combined


def test_chunk_never_crosses_a_chapter_boundary():
    blocks = [
        _chapter_block("9", "Heart Muscle", 1),
        _body_block(_sentence(5), 1),
        _chapter_block("10", "Rhythmical Excitation", 2),
        _body_block(_sentence(5), 2),
    ]
    chunker = _chunker(target=1000, max_tokens=2000)  # budget big enough it would never force-split

    chunks = chunker.chunk(_DOCUMENT_ID, Subject.PHYSIOLOGY, "Physiology", "14th", blocks)

    chapters_per_chunk = {c.metadata.chunk_index: c.metadata.chapter_number for c in chunks}
    assert set(chapters_per_chunk.values()) == {"9", "10"}
    for chunk in chunks:
        assert "CHAPTER 9" not in chunk.text or "CHAPTER 10" not in chunk.text


def test_no_overlap_carried_across_chapter_boundary():
    blocks = [
        _chapter_block("9", "Heart Muscle", 1),
        _body_block("UNIQUE_CHAPTER_NINE_MARKER " + _sentence(30), 1),
        _chapter_block("10", "Rhythmical Excitation", 2),
        _body_block(_sentence(10), 2),
    ]
    chunker = _chunker(target=20, max_tokens=40, overlap=15)

    chunks = chunker.chunk(_DOCUMENT_ID, Subject.PHYSIOLOGY, "Physiology", "14th", blocks)

    chapter_10_chunks = [c for c in chunks if c.metadata.chapter_number == "10"]
    assert all("UNIQUE_CHAPTER_NINE_MARKER" not in c.text for c in chapter_10_chunks)


def test_overlap_present_between_forced_within_chapter_splits():
    # Each individual block (~35 tokens) stays well under max_tokens on its
    # own — this exercises the "buffer would overflow if we add the next
    # block" forced flush, not the separate single-oversized-block path.
    blocks = [
        _chapter_block("9", "Heart Muscle", 1),
        _body_block("MARKER_ALPHA " + _sentence(3), 1),
        _body_block("MARKER_BETA " + _sentence(3), 1),
        _body_block("MARKER_GAMMA " + _sentence(3), 1),
    ]
    chunker = _chunker(target=40, max_tokens=120, overlap=15)

    chunks = chunker.chunk(_DOCUMENT_ID, Subject.PHYSIOLOGY, "Physiology", "14th", blocks)

    assert len(chunks) >= 2
    assert "MARKER_ALPHA" in chunks[0].text
    assert "MARKER_GAMMA" in chunks[-1].text
    # the overlap window carried from the tail of chunk 0 into the start of
    # chunk 1's body — verify the mechanism directly rather than assuming
    # exactly which marker word ends up inside the (token-approximate,
    # character-based) overlap window.
    tail_of_first = chunks[0].text[-60:]
    assert tail_of_first.strip()
    assert tail_of_first in chunks[1].text


def test_metadata_page_range_reflects_first_and_last_block():
    blocks = [
        _chapter_block("9", "Heart Muscle", 5),
        _body_block(_sentence(3), 5),
        _body_block(_sentence(3), 6),
        _body_block(_sentence(3), 7),
    ]
    chunker = _chunker(target=1000, max_tokens=2000)

    chunks = chunker.chunk(_DOCUMENT_ID, Subject.PHYSIOLOGY, "Physiology", "14th", blocks)

    assert len(chunks) == 1
    assert chunks[0].metadata.pdf_page_start == 5
    assert chunks[0].metadata.pdf_page_end == 7


def test_chunk_index_is_sequential_from_zero():
    blocks = [
        _chapter_block("9", "Heart Muscle", 1),
        _body_block(_sentence(10), 1),
        _chapter_block("10", "Rhythmical Excitation", 2),
        _body_block(_sentence(10), 2),
    ]
    chunker = _chunker(target=1000, max_tokens=2000)

    chunks = chunker.chunk(_DOCUMENT_ID, Subject.PHYSIOLOGY, "Physiology", "14th", blocks)

    assert [c.metadata.chunk_index for c in chunks] == list(range(len(chunks)))


def test_short_but_real_definition_is_retained():
    definition = (
        "Homeostasis is the maintenance of a stable internal environment despite external change."
    )
    blocks = [_chapter_block("1", "Introduction", 1), _body_block(definition, 1)]
    chunker = _chunker(target=1000, max_tokens=2000, min_useful=20)

    chunks = chunker.chunk(_DOCUMENT_ID, Subject.PHYSIOLOGY, "Physiology", "14th", blocks)

    combined = " ".join(c.text for c in chunks)
    assert "Homeostasis" in combined


def test_pure_noise_chunk_is_dropped():
    blocks = [
        _chapter_block("1", "Introduction", 1),
        _body_block("Contents", 1),
    ]
    chunker = _chunker(target=1000, max_tokens=2000)

    chunks = chunker.chunk(_DOCUMENT_ID, Subject.PHYSIOLOGY, "Physiology", "14th", blocks)

    assert not any(c.text.strip() == "Contents" for c in chunks)


def test_figure_caption_recorded_in_metadata():
    blocks = [
        _chapter_block("9", "Heart Muscle", 1),
        _body_block(_sentence(5), 1),
        _body_block("Fig. 9.1: The cardiac cycle.", 1, is_caption=True),
        _body_block(_sentence(5), 1),
    ]
    chunker = _chunker(target=1000, max_tokens=2000)

    chunks = chunker.chunk(_DOCUMENT_ID, Subject.PHYSIOLOGY, "Physiology", "14th", blocks)

    assert any("Fig. 9.1" in ref for c in chunks for ref in c.metadata.figure_references)


def test_context_prefix_present_for_content_chunks():
    blocks = [
        _chapter_block("9", "Heart Muscle", 1),
        _heading_block("The Cardiac Cycle", 1),
        _body_block(_sentence(20), 1),
    ]
    chunker = _chunker()  # defaults are enough — every finalized chunk gets a prefix

    chunks = chunker.chunk(_DOCUMENT_ID, Subject.PHYSIOLOGY, "Physiology", "14th", blocks)

    assert any("Chapter 9" in c.text for c in chunks)


def test_token_count_matches_count_tokens_of_chunk_text():
    blocks = [_chapter_block("9", "Heart Muscle", 1), _body_block(_sentence(20), 1)]
    chunker = _chunker(target=1000, max_tokens=2000)

    chunks = chunker.chunk(_DOCUMENT_ID, Subject.PHYSIOLOGY, "Physiology", "14th", blocks)

    for chunk in chunks:
        assert chunk.metadata.token_count == count_tokens(chunk.text)


def test_chunker_rejects_invalid_configuration():
    with pytest.raises(ValueError):
        TextbookChunker(target_tokens=100, max_tokens=50, overlap_tokens=10, min_useful_tokens=5)
    with pytest.raises(ValueError):
        TextbookChunker(target_tokens=50, max_tokens=100, overlap_tokens=50, min_useful_tokens=5)
