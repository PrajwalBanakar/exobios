from app.ingestion.cleaning.text_cleaner import TextCleaner
from app.ingestion.parsers.base import ParsedPage


def test_normalizes_whitespace_without_touching_words():
    pages = [ParsedPage(page_number=1, text="Dose:   500mg   b.i.d.\n\n\n\nNext line")]

    cleaned = TextCleaner().clean_pages(pages)

    assert cleaned[0].text == "Dose: 500mg b.i.d.\n\nNext line"


def test_preserves_bullet_lists_and_numbering():
    text = "Symptoms:\n- fever\n- cough\n\nPlan:\n1. Rest\n2. Fluids"
    pages = [ParsedPage(page_number=1, text=text)]

    cleaned = TextCleaner().clean_pages(pages)

    assert "- fever" in cleaned[0].text
    assert "- cough" in cleaned[0].text
    assert "1. Rest" in cleaned[0].text
    assert "2. Fluids" in cleaned[0].text


def test_strips_repeated_headers_and_footers_across_pages():
    pages = [
        ParsedPage(page_number=1, text="CONFIDENTIAL\nBody text one\nPage 1"),
        ParsedPage(page_number=2, text="CONFIDENTIAL\nBody text two\nPage 2"),
        ParsedPage(page_number=3, text="CONFIDENTIAL\nBody text three\nPage 3"),
    ]

    cleaned = TextCleaner().clean_pages(pages)

    for page in cleaned:
        assert "CONFIDENTIAL" not in page.text
    assert "Body text one" in cleaned[0].text
    assert "Body text two" in cleaned[1].text


def test_leaves_short_document_headers_untouched():
    pages = [
        ParsedPage(page_number=1, text="CONFIDENTIAL\nBody one"),
        ParsedPage(page_number=2, text="CONFIDENTIAL\nBody two"),
    ]

    cleaned = TextCleaner().clean_pages(pages)

    assert cleaned[0].text.startswith("CONFIDENTIAL")
