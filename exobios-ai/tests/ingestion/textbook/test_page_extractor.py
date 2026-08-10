from uuid import uuid4

import fitz
import pytest

from app.ingestion.exceptions import DocumentParseError
from app.ingestion.textbook.exceptions import EncryptedDocumentError
from app.ingestion.textbook.models import ExtractionStatus, HeadingLevel, PageClassification
from app.ingestion.textbook.page_extractor import TextbookPageExtractor


def test_preserves_pdf_page_boundaries(pdf_builder, body_paragraph):
    content = pdf_builder([body_paragraph(72), body_paragraph(72), body_paragraph(72)])

    output = TextbookPageExtractor().extract(uuid4(), content)

    assert [page.pdf_page_number for page in output.pages] == [1, 2, 3]


def test_blank_page_extraction_status_is_sparse(pdf_builder):
    content = pdf_builder([[]])  # one page, no content at all

    output = TextbookPageExtractor().extract(uuid4(), content)

    assert output.pages[0].extraction_status == ExtractionStatus.TEXT_SPARSE


def test_text_page_extraction_status_is_ok(pdf_builder, body_paragraph):
    content = pdf_builder([body_paragraph(72)])

    output = TextbookPageExtractor().extract(uuid4(), content)

    assert output.pages[0].extraction_status == ExtractionStatus.TEXT_OK
    assert "cardiac cycle" in output.pages[0].raw_text.lower()


def test_malformed_pdf_raises_document_parse_error():
    with pytest.raises(DocumentParseError):
        TextbookPageExtractor().extract(uuid4(), b"not a pdf at all")


def test_encrypted_pdf_raises_encrypted_document_error():
    document = fitz.open()
    document.new_page().insert_text((72, 72), "secret", fontsize=12)
    content = document.tobytes(
        encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="owner123", user_pw="user123"
    )
    document.close()

    with pytest.raises(EncryptedDocumentError):
        TextbookPageExtractor().extract(uuid4(), content)


def test_chapter_heading_detected_via_keyword(pdf_builder, body_paragraph):
    content = pdf_builder(
        [[("CHAPTER 9 Heart Muscle and the Cardiac Pump", 18, 72, 72), *body_paragraph(110)]]
    )

    output = TextbookPageExtractor().extract(uuid4(), content)

    headings = [h for h in output.pages[0].headings if h.level == HeadingLevel.CHAPTER]
    assert len(headings) == 1
    assert headings[0].number == "9"
    assert "Heart Muscle" in headings[0].text


def test_unit_section_heading_detected_via_keyword(pdf_builder, body_paragraph):
    content = pdf_builder([[("UNIT III The Heart", 18, 72, 72), *body_paragraph(110)]])

    output = TextbookPageExtractor().extract(uuid4(), content)

    headings = [h for h in output.pages[0].headings if h.level == HeadingLevel.UNIT_SECTION]
    assert len(headings) == 1
    assert headings[0].number.upper() == "III"
    assert headings[0].text == "The Heart"


def test_font_based_heading_detected_for_short_large_line(pdf_builder, body_paragraph):
    content = pdf_builder([[("The Cardiac Cycle", 16, 72, 72), *body_paragraph(110)]])

    output = TextbookPageExtractor().extract(uuid4(), content)

    headings = output.pages[0].headings
    assert any(h.text == "The Cardiac Cycle" for h in headings)


def test_font_based_heading_text_has_internal_newlines_collapsed(pdf_builder, body_paragraph):
    # A subheading wrapped across two lines by the PDF layout is one
    # PyMuPDF block with an embedded "\n" — section_title/subsection_title
    # are stored metadata, not flowing body text, and should read as one
    # clean line rather than leak the raw line break.
    content = pdf_builder(
        [
            [
                ("The Cardiac", 16, 72, 72),
                ("Cycle", 16, 72, 90),
                *body_paragraph(130),
            ]
        ]
    )

    output = TextbookPageExtractor().extract(uuid4(), content)

    headings = [h.text for h in output.pages[0].headings]
    assert "The Cardiac Cycle" in headings
    assert not any("\n" in text for text in headings)


def test_no_heading_invented_for_plain_body_paragraph(pdf_builder, body_paragraph):
    content = pdf_builder([body_paragraph(72)])

    output = TextbookPageExtractor().extract(uuid4(), content)

    assert output.pages[0].headings == []
    assert all(block.heading is None for block in output.blocks)


def test_printed_page_number_detected_in_footer_zone(pdf_builder, body_paragraph):
    content = pdf_builder([[*body_paragraph(72), ("106", 9, 300, 820)]])

    output = TextbookPageExtractor().extract(uuid4(), content)

    assert output.pages[0].printed_page_number == 106
    # every real content block on the page should carry it, not just
    # whichever ones happened to be extracted after the footer block
    assert all(
        block.printed_page_number == 106 for block in output.blocks if block.pdf_page_number == 1
    )


def test_printed_page_number_is_none_when_absent(pdf_builder, body_paragraph):
    content = pdf_builder([body_paragraph(72)])

    output = TextbookPageExtractor().extract(uuid4(), content)

    assert output.pages[0].printed_page_number is None


def test_bare_page_number_is_not_emitted_as_a_content_block(pdf_builder, body_paragraph):
    content = pdf_builder([[*body_paragraph(72), ("106", 9, 300, 820)]])

    output = TextbookPageExtractor().extract(uuid4(), content)

    assert not any(block.text.strip() == "106" for block in output.blocks)


def test_chapter_title_on_separate_line_is_merged_into_chapter_title(pdf_builder, body_paragraph):
    content = pdf_builder(
        [
            [
                ("CHAPTER 9", 20, 72, 72),
                ("Heart Muscle; The Heart as a Pump", 16, 72, 105),
                *body_paragraph(140),
            ]
        ]
    )

    output = TextbookPageExtractor().extract(uuid4(), content)

    chapter_headings = [h for h in output.pages[0].headings if h.level == HeadingLevel.CHAPTER]
    assert len(chapter_headings) == 1
    assert chapter_headings[0].number == "9"
    assert chapter_headings[0].text == "Heart Muscle; The Heart as a Pump"
    assert output.pages[0].structure_after.chapter_title == "Heart Muscle; The Heart as a Pump"


def test_structure_state_carries_across_pages(pdf_builder, body_paragraph):
    content = pdf_builder(
        [
            [("CHAPTER 4 The Axilla", 18, 72, 72), *body_paragraph(110)],
            body_paragraph(72),  # page 2: no new heading at all
        ]
    )

    output = TextbookPageExtractor().extract(uuid4(), content)

    assert output.pages[1].structure_after.chapter_number == "4"
    assert output.pages[1].structure_after.chapter_title == "The Axilla"


def test_new_chapter_resets_section_and_subsection_state(pdf_builder, body_paragraph):
    content = pdf_builder(
        [
            [
                ("CHAPTER 9 Heart Muscle", 18, 72, 72),
                ("The Cardiac Cycle", 15, 72, 110),
                *body_paragraph(140),
            ],
            [("CHAPTER 10 Rhythmical Excitation", 18, 72, 72), *body_paragraph(110)],
        ]
    )

    output = TextbookPageExtractor().extract(uuid4(), content)

    assert output.pages[0].structure_after.section_title == "The Cardiac Cycle"
    assert output.pages[1].structure_after.chapter_number == "10"
    assert output.pages[1].structure_after.section_title is None


def test_main_content_zone_starts_at_first_chapter(pdf_builder, body_paragraph):
    content = pdf_builder(
        [
            body_paragraph(72),  # front matter — no chapter yet
            [("CHAPTER 1 Introduction", 18, 72, 72), *body_paragraph(110)],
        ]
    )

    output = TextbookPageExtractor().extract(uuid4(), content)

    assert output.pages[0].classification == PageClassification.FRONT_MATTER
    assert output.pages[1].classification == PageClassification.MAIN_CONTENT


def test_running_header_repeated_on_every_page_is_not_treated_as_a_heading(
    pdf_builder, body_paragraph
):
    # A book title styled in a larger font and printed identically on every
    # page is a running header, not real structure — it must not pollute
    # section_title on every chunk in the book.
    content = pdf_builder(
        [[("Human Anatomy – Neuroanatomy", 14, 400, 50), *body_paragraph(72)] for _ in range(12)]
    )

    output = TextbookPageExtractor().extract(uuid4(), content)

    assert not any(
        block.heading is not None and block.heading.text == "Human Anatomy – Neuroanatomy"
        for block in output.blocks
    )
    # the text itself is still present in the document, just not as a heading
    assert any("Human Anatomy" in block.text for block in output.blocks)


def test_toc_mentioning_appendix_does_not_flip_the_whole_book_to_appendix(
    pdf_builder, body_paragraph
):
    # A table-of-contents line listing an appendix entry, on the very first
    # page, before any real chapter has started — must not stick the zone
    # classification at APPENDIX for the rest of the book.
    content = pdf_builder(
        [
            [("Appendix: Ventricles, Cranial Nerves and Arteries", 13, 72, 72)],
            [("CHAPTER 1 Organisation of Nervous System", 18, 72, 72), *body_paragraph(110)],
        ]
    )

    output = TextbookPageExtractor().extract(uuid4(), content)

    assert output.pages[0].classification == PageClassification.FRONT_MATTER
    assert output.pages[1].classification == PageClassification.MAIN_CONTENT


def test_a_bad_page_does_not_abort_the_whole_document(pdf_builder, body_paragraph, monkeypatch):
    content = pdf_builder([body_paragraph(72), body_paragraph(72)])

    original_get_text = fitz.Page.get_text
    state = {"failed_once": False}

    def flaky_get_text(self, *args, **kwargs):
        mode = args[0] if args else kwargs.get("option")
        if mode == "text" and not state["failed_once"]:
            state["failed_once"] = True
            raise RuntimeError("simulated extraction failure")
        return original_get_text(self, *args, **kwargs)

    monkeypatch.setattr(fitz.Page, "get_text", flaky_get_text)

    output = TextbookPageExtractor().extract(uuid4(), content)

    assert len(output.pages) == 2
    assert output.pages[0].extraction_status == ExtractionStatus.EXTRACTION_FAILED
    # page 2's plain "text" extraction succeeds normally afterward
    assert output.pages[1].extraction_status == ExtractionStatus.TEXT_OK
