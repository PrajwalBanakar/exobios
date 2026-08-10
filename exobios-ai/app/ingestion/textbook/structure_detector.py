import re

from app.ingestion.textbook.models import DetectedHeading, HeadingLevel, StructureState

# CHAPTER is the highest-confidence signal: an explicit keyword + number.
# Matches "Chapter 4", "CHAPTER 9", "Chapter 13: Metabolism of Carbohydrates".
_CHAPTER_RE = re.compile(r"^chapter\s+(\d{1,3})\b\s*[:.\-–—]?\s*(.*)$", re.IGNORECASE)

# UNIT/SECTION groups span multiple chapters. The number token is captured
# raw (roman numeral, word-form, or digit) and never converted — e.g.
# "UNIT III", "SECTION THREE", "Section 1" all just store their own token.
#
# The word-form alternative is an explicit enumeration (ONE..TWENTY), not a
# bare [a-z]+ catch-all: real books are full of ordinary sentences starting
# "Section of the ..." (e.g. a figure caption, "Section of the human
# kidney showing...") — an unrestricted word match turned every one of
# those into a fake UNIT_SECTION heading during real-book validation.
_NUMBER_WORDS = (
    "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    "fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty"
)
_UNIT_SECTION_RE = re.compile(
    rf"^(?:unit|section)\s+([ivxlcdm]+|{_NUMBER_WORDS}|\d{{1,3}})\b\s*[:.\-–—]?\s*(.*)$",
    re.IGNORECASE,
)

# A line matching one of these, when it's the *entire* line, is treated as
# a bare page number / roman-numeral folio rather than heading content —
# never a heading candidate even if its font size is elevated.
_PAGE_NUMBER_ONLY_RE = re.compile(r"^\s*[ivxlcdm]{1,7}\s*$|^\s*\d{1,4}\s*$", re.IGNORECASE)

_MAX_HEADING_LENGTH = 100
_MIN_HEADING_ALPHA_CHARS = 3

# Font-size tiers, relative to the document's body-text font size. These are
# heuristic multipliers, not a guarantee — real textbooks vary in
# typography, and this is a best-effort deterministic signal, not a layout
# parser. Tune here if real-book validation shows a book's headings are
# consistently mis-tiered.
_HEADING_FONT_RATIO = 1.30
_SUBHEADING_FONT_RATIO = 1.12


def _title_from_continuation_lines(lines: list[str]) -> str:
    """Real PDFs often merge "Chapter 9", its title, and a stray trailing
    page-number fragment into one multi-line PyMuPDF block (as opposed to
    separate blocks — see _merge_chapter_title_continuations in
    page_extractor.py for that case). Join whatever isn't itself a bare
    folio number into the title."""
    kept = [line for line in lines if not _PAGE_NUMBER_ONLY_RE.match(line)]
    return " ".join(kept).strip()


def match_keyword_heading(text: str) -> DetectedHeading | None:
    """Highest-confidence structural match: an explicit CHAPTER/UNIT/SECTION
    keyword followed by a number. Returns None for anything else — this
    function never guesses.

    Only the block's first physical line is tested against the keyword
    patterns (a block can legitimately contain several unrelated lines —
    "Chapter 9", its title, and a trailing page-number token all merged by
    PyMuPDF into one block); if that line captures no title of its own, the
    remaining lines (minus any bare folio numbers) are joined into one.
    """
    stripped = text.strip()
    if not stripped:
        return None

    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    if not lines:
        return None
    first_line = lines[0]

    chapter_match = _CHAPTER_RE.match(first_line)
    if chapter_match:
        number = chapter_match.group(1)
        title = chapter_match.group(2).strip() or _title_from_continuation_lines(lines[1:])
        return DetectedHeading(level=HeadingLevel.CHAPTER, text=title, number=number)

    unit_match = _UNIT_SECTION_RE.match(first_line)
    if unit_match:
        number = unit_match.group(1)
        title = unit_match.group(2).strip() or _title_from_continuation_lines(lines[1:])
        return DetectedHeading(level=HeadingLevel.UNIT_SECTION, text=title, number=number)

    return None


def classify_font_heading(
    text: str, font_size: float, body_font_size: float
) -> HeadingLevel | None:
    """Best-effort generic heading detection for headings with no keyword
    prefix (e.g. "Brachial Plexus", "The Cardiac Cycle") — a short line set
    in a meaningfully larger font than the document's body text. Returns
    None (never a guess) when the line looks like body text, a caption, or
    a bare page number."""
    stripped = text.strip()
    if not stripped or len(stripped) > _MAX_HEADING_LENGTH:
        return None
    if _PAGE_NUMBER_ONLY_RE.match(stripped):
        return None
    if sum(1 for c in stripped if c.isalpha()) < _MIN_HEADING_ALPHA_CHARS:
        return None
    if body_font_size <= 0:
        return None

    ratio = font_size / body_font_size
    if ratio >= _HEADING_FONT_RATIO:
        return HeadingLevel.HEADING
    if ratio >= _SUBHEADING_FONT_RATIO:
        return HeadingLevel.SUBHEADING
    return None


class StructureTracker:
    """Maintains running StructureState across an entire document's block
    stream, in reading order. A CHAPTER heading resets section/subsection
    (a new chapter starts with no section yet); a UNIT_SECTION heading
    resets chapter/section/subsection too (a new unit-level grouping starts
    fresh); a HEADING resets only subsection; a SUBHEADING updates only
    itself. State never resets on page boundaries — it's a document-wide
    running position, not a per-page one.
    """

    def __init__(self) -> None:
        self._state = StructureState()

    @property
    def state(self) -> StructureState:
        return self._state

    def apply(self, heading: DetectedHeading) -> StructureState:
        if heading.level is HeadingLevel.UNIT_SECTION:
            self._state = StructureState(unit_or_section=heading.text or heading.number)
        elif heading.level is HeadingLevel.CHAPTER:
            self._state = StructureState(
                unit_or_section=self._state.unit_or_section,
                chapter_number=heading.number,
                chapter_title=heading.text or None,
            )
        elif heading.level is HeadingLevel.HEADING:
            self._state = self._state.model_copy(
                update={"section_title": heading.text, "subsection_title": None}
            )
        elif heading.level is HeadingLevel.SUBHEADING:
            self._state = self._state.model_copy(update={"subsection_title": heading.text})
        return self._state
