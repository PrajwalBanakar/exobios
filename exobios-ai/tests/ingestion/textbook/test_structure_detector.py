from app.ingestion.textbook.models import DetectedHeading, HeadingLevel
from app.ingestion.textbook.structure_detector import (
    StructureTracker,
    classify_font_heading,
    match_keyword_heading,
)


def test_match_keyword_heading_detects_chapter():
    heading = match_keyword_heading("Chapter 13: Metabolism of Carbohydrates")

    assert heading is not None
    assert heading.level == HeadingLevel.CHAPTER
    assert heading.number == "13"
    assert heading.text == "Metabolism of Carbohydrates"


def test_match_keyword_heading_detects_uppercase_chapter():
    heading = match_keyword_heading("CHAPTER 9 Heart Muscle; The Heart as a Pump")

    assert heading is not None
    assert heading.level == HeadingLevel.CHAPTER
    assert heading.number == "9"


def test_match_keyword_heading_detects_unit():
    heading = match_keyword_heading("UNIT III — The Heart")

    assert heading is not None
    assert heading.level == HeadingLevel.UNIT_SECTION
    assert heading.number.upper() == "III"
    assert heading.text == "The Heart"


def test_match_keyword_heading_detects_word_form_section_number():
    heading = match_keyword_heading("SECTION THREE — Metabolism")

    assert heading is not None
    assert heading.level == HeadingLevel.UNIT_SECTION
    assert heading.number.upper() == "THREE"
    assert heading.text == "Metabolism"


def test_match_keyword_heading_handles_multiline_block_with_trailing_page_number():
    # Real books frequently have PyMuPDF merge "Chapter N", its title, and a
    # stray trailing folio number into one multi-line block.
    heading = match_keyword_heading(
        "Chapter 1\nFunctional Organization of the Human Body and Control "
        'of the "Internal Environment"\n5'
    )

    assert heading is not None
    assert heading.level == HeadingLevel.CHAPTER
    assert heading.number == "1"
    assert (
        heading.text
        == 'Functional Organization of the Human Body and Control of the "Internal Environment"'
    )


def test_match_keyword_heading_returns_none_for_body_text():
    assert match_keyword_heading("The brachial plexus arises from spinal nerves C5-T1.") is None


def test_match_keyword_heading_returns_none_for_blank_text():
    assert match_keyword_heading("   ") is None


def test_match_keyword_heading_does_not_treat_arbitrary_words_as_section_numbers():
    # Found during real-book validation: an unrestricted word match here
    # turned figure captions like this into fake UNIT_SECTION headings.
    assert match_keyword_heading("Section of the human kidney showing the major vessels") is None


def test_match_keyword_heading_word_form_number_is_restricted_to_a_known_list():
    assert match_keyword_heading("Section Twenty: Endocrine Glands") is not None
    assert match_keyword_heading("Section Blahblah: Not A Real Number") is None


def test_classify_font_heading_detects_heading_tier():
    level = classify_font_heading("Brachial Plexus", font_size=16.0, body_font_size=10.0)

    assert level == HeadingLevel.HEADING


def test_classify_font_heading_detects_subheading_tier():
    level = classify_font_heading("Clinical Anatomy", font_size=11.5, body_font_size=10.0)

    assert level == HeadingLevel.SUBHEADING


def test_classify_font_heading_returns_none_for_body_sized_text():
    level = classify_font_heading(
        "This sentence is set in the same size as ordinary body text.",
        font_size=10.0,
        body_font_size=10.0,
    )

    assert level is None


def test_classify_font_heading_returns_none_for_bare_page_number():
    assert classify_font_heading("42", font_size=20.0, body_font_size=10.0) is None


def test_classify_font_heading_returns_none_for_overly_long_line():
    long_line = "A " * 60  # way over the heading length ceiling
    assert classify_font_heading(long_line, font_size=20.0, body_font_size=10.0) is None


def test_classify_font_heading_returns_none_when_body_font_size_unknown():
    assert classify_font_heading("Brachial Plexus", font_size=16.0, body_font_size=0.0) is None


def test_structure_tracker_chapter_resets_section_and_subsection():
    tracker = StructureTracker()
    tracker.apply(DetectedHeading(level=HeadingLevel.HEADING, text="Old Section"))
    tracker.apply(DetectedHeading(level=HeadingLevel.SUBHEADING, text="Old Subsection"))

    state = tracker.apply(DetectedHeading(level=HeadingLevel.CHAPTER, number="9", text="Heart"))

    assert state.chapter_number == "9"
    assert state.chapter_title == "Heart"
    assert state.section_title is None
    assert state.subsection_title is None


def test_structure_tracker_unit_resets_chapter_and_section():
    tracker = StructureTracker()
    tracker.apply(DetectedHeading(level=HeadingLevel.CHAPTER, number="4", text="The Axilla"))
    tracker.apply(DetectedHeading(level=HeadingLevel.HEADING, text="Brachial Plexus"))

    state = tracker.apply(
        DetectedHeading(level=HeadingLevel.UNIT_SECTION, number="III", text="The Heart")
    )

    assert state.unit_or_section == "The Heart"
    assert state.chapter_number is None
    assert state.section_title is None


def test_structure_tracker_heading_resets_only_subsection():
    tracker = StructureTracker()
    tracker.apply(DetectedHeading(level=HeadingLevel.CHAPTER, number="9", text="Heart Muscle"))
    tracker.apply(DetectedHeading(level=HeadingLevel.HEADING, text="The Cardiac Cycle"))
    tracker.apply(DetectedHeading(level=HeadingLevel.SUBHEADING, text="Diastole"))

    state = tracker.apply(DetectedHeading(level=HeadingLevel.HEADING, text="Heart Sounds"))

    assert state.chapter_number == "9"  # untouched
    assert state.section_title == "Heart Sounds"
    assert state.subsection_title is None


def test_structure_tracker_subheading_only_updates_subsection():
    tracker = StructureTracker()
    tracker.apply(DetectedHeading(level=HeadingLevel.CHAPTER, number="9", text="Heart Muscle"))
    tracker.apply(DetectedHeading(level=HeadingLevel.HEADING, text="The Cardiac Cycle"))

    state = tracker.apply(DetectedHeading(level=HeadingLevel.SUBHEADING, text="Diastole"))

    assert state.chapter_number == "9"
    assert state.section_title == "The Cardiac Cycle"
    assert state.subsection_title == "Diastole"


def test_structure_tracker_unit_persists_across_chapters():
    tracker = StructureTracker()
    tracker.apply(DetectedHeading(level=HeadingLevel.UNIT_SECTION, number="III", text="The Heart"))
    tracker.apply(DetectedHeading(level=HeadingLevel.CHAPTER, number="9", text="Heart Muscle"))

    state = tracker.apply(
        DetectedHeading(level=HeadingLevel.CHAPTER, number="10", text="Rhythmical Excitation")
    )

    assert state.unit_or_section == "The Heart"
    assert state.chapter_number == "10"
