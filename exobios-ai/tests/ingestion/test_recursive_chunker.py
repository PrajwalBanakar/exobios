from uuid import uuid4

import pytest

from app.ingestion.chunkers.recursive_chunker import RecursiveChunker
from app.ingestion.exceptions import ChunkingError
from app.ingestion.parsers.base import ParsedPage


def test_short_text_produces_a_single_chunk():
    document_id = uuid4()
    pages = [ParsedPage(page_number=1, text="A short sentence.")]

    chunks = RecursiveChunker(chunk_size=1000, chunk_overlap=100).chunk(document_id, pages)

    assert len(chunks) == 1
    assert chunks[0].text == "A short sentence."
    assert chunks[0].metadata.document_id == document_id
    assert chunks[0].metadata.page_number == 1
    assert chunks[0].metadata.chunk_number == 1
    assert chunks[0].metadata.start_offset == 0
    assert chunks[0].metadata.end_offset == len("A short sentence.")


def test_long_text_is_split_with_overlap_and_valid_offsets():
    document_id = uuid4()
    text = ("0123456789" * 20) + " " + ("abcdefghij" * 20)
    pages = [ParsedPage(page_number=1, text=text)]

    chunks = RecursiveChunker(chunk_size=50, chunk_overlap=10).chunk(document_id, pages)

    assert len(chunks) > 1
    for index, chunk in enumerate(chunks, start=1):
        assert chunk.metadata.chunk_number == index
        assert chunk.metadata.start_offset < chunk.metadata.end_offset
        assert chunk.metadata.end_offset <= len(text)
        assert chunk.text == text[chunk.metadata.start_offset : chunk.metadata.end_offset]

    for previous, current in zip(chunks, chunks[1:], strict=False):
        assert current.metadata.start_offset < previous.metadata.end_offset


def test_chunk_numbers_are_sequential_across_pages():
    document_id = uuid4()
    pages = [
        ParsedPage(page_number=1, text="Page one text."),
        ParsedPage(page_number=2, text="Page two text."),
    ]

    chunks = RecursiveChunker(chunk_size=1000, chunk_overlap=100).chunk(document_id, pages)

    assert [c.metadata.chunk_number for c in chunks] == [1, 2]
    assert [c.metadata.page_number for c in chunks] == [1, 2]


def test_detects_markdown_heading_as_section_title():
    document_id = uuid4()
    filler = "word " * 40
    text = f"# Diagnosis\n\n{filler}"
    pages = [ParsedPage(page_number=1, text=text)]

    # Small chunk_size forces the heading and the body into separate chunks,
    # so the body chunk's start_offset is past the heading line and lookback
    # detection has something to scan.
    chunks = RecursiveChunker(chunk_size=50, chunk_overlap=0).chunk(document_id, pages)

    assert len(chunks) > 1
    assert chunks[-1].metadata.section_title == "Diagnosis"


def test_blank_pages_are_skipped():
    document_id = uuid4()
    pages = [ParsedPage(page_number=1, text="   \n  "), ParsedPage(page_number=2, text="Real text")]

    chunks = RecursiveChunker(chunk_size=1000, chunk_overlap=100).chunk(document_id, pages)

    assert len(chunks) == 1
    assert chunks[0].metadata.page_number == 2


def test_raises_chunking_error_when_no_text_available():
    document_id = uuid4()
    pages = [ParsedPage(page_number=1, text="   ")]

    with pytest.raises(ChunkingError):
        RecursiveChunker().chunk(document_id, pages)


def test_rejects_invalid_chunk_size():
    with pytest.raises(ChunkingError):
        RecursiveChunker(chunk_size=0)


def test_rejects_overlap_not_smaller_than_chunk_size():
    with pytest.raises(ChunkingError):
        RecursiveChunker(chunk_size=100, chunk_overlap=100)
