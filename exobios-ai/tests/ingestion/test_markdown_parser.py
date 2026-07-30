import pytest

from app.ingestion.exceptions import DocumentParseError
from app.ingestion.parsers.markdown_parser import MarkdownParser


def test_markdown_parser_preserves_headings_and_lists():
    content = (
        b"# Diagnosis\n\n- fever\n- cough\n\n1. Rest\n2. Hydration\n"
    )

    parsed = MarkdownParser().parse(content, "notes.md")

    assert len(parsed.pages) == 1
    text = parsed.pages[0].text
    assert "# Diagnosis" in text
    assert "- fever" in text
    assert "1. Rest" in text


def test_markdown_parser_rejects_empty_file():
    with pytest.raises(DocumentParseError):
        MarkdownParser().parse(b"", "empty.md")
