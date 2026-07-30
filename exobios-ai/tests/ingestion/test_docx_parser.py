import pytest

from app.ingestion.exceptions import DocumentParseError
from app.ingestion.parsers.docx_parser import DocxParser


def test_docx_parser_extracts_paragraph_text(docx_bytes_factory):
    content = docx_bytes_factory(["First paragraph.", "Second paragraph."])

    parsed = DocxParser().parse(content, "sample.docx")

    assert len(parsed.pages) == 1
    assert parsed.pages[0].page_number == 1
    assert "First paragraph." in parsed.pages[0].text
    assert "Second paragraph." in parsed.pages[0].text


def test_docx_parser_rejects_corrupt_docx():
    with pytest.raises(DocumentParseError):
        DocxParser().parse(b"not a real docx", "broken.docx")


def test_docx_parser_rejects_empty_document(docx_bytes_factory):
    content = docx_bytes_factory([])

    with pytest.raises(DocumentParseError):
        DocxParser().parse(content, "empty.docx")
