import pytest

from app.ingestion.exceptions import DocumentParseError
from app.ingestion.parsers.pdf_parser import PdfParser


def test_pdf_parser_extracts_pages_in_order(pdf_bytes_factory):
    content = pdf_bytes_factory(["Page one content", "Page two content"])

    parsed = PdfParser().parse(content, "sample.pdf")

    assert [page.page_number for page in parsed.pages] == [1, 2]
    assert "Page one" in parsed.pages[0].text
    assert "Page two" in parsed.pages[1].text


def test_pdf_parser_rejects_corrupt_pdf():
    with pytest.raises(DocumentParseError):
        PdfParser().parse(b"not a real pdf", "broken.pdf")
