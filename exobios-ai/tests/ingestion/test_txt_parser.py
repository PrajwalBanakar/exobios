import pytest

from app.ingestion.exceptions import DocumentParseError
from app.ingestion.parsers.txt_parser import TxtParser


def test_txt_parser_extracts_single_page():
    content = b"Patient reports fever and cough."

    parsed = TxtParser().parse(content, "note.txt")

    assert len(parsed.pages) == 1
    assert parsed.pages[0].page_number == 1
    assert parsed.pages[0].text == "Patient reports fever and cough."


def test_txt_parser_rejects_empty_file():
    with pytest.raises(DocumentParseError):
        TxtParser().parse(b"   \n  ", "empty.txt")


def test_txt_parser_replaces_undecodable_bytes():
    content = b"valid text \xff\xfe more text"

    parsed = TxtParser().parse(content, "note.txt")

    assert "valid text" in parsed.pages[0].text
