import logging
import re
from collections import Counter
from dataclasses import dataclass
from itertools import groupby
from uuid import UUID

import fitz

from app.ingestion.cleaning.text_cleaner import TextCleaner
from app.ingestion.exceptions import DocumentParseError
from app.ingestion.parsers.base import ParsedPage
from app.ingestion.textbook.exceptions import EncryptedDocumentError
from app.ingestion.textbook.models import (
    ContentBlock,
    DetectedHeading,
    ExtractionStatus,
    HeadingLevel,
    PageClassification,
    PageExtraction,
    StructureState,
)
from app.ingestion.textbook.structure_detector import (
    StructureTracker,
    classify_font_heading,
    match_keyword_heading,
)

logger = logging.getLogger("app.ingestion.textbook")

_MIN_CHARS_TEXT_OK = 40
_PAGE_NUMBER_ZONE_RATIO = 0.08  # top/bottom 8% of page height counts as a folio zone
_PRINTED_PAGE_NUMBER_RE = re.compile(r"^\d{1,4}$")
_CAPTION_RE = re.compile(r"^(fig\.?|figure|table)\s*\d+[.:]", re.IGNORECASE)
_APPENDIX_RE = re.compile(r"\bappendix\b", re.IGNORECASE)
_INDEX_HEADING_RE = re.compile(r"^\s*index\s*$", re.IGNORECASE)
_QUESTIONS_HEADING_RE = re.compile(
    r"^\s*(review\s+questions|self[- ]assessment|"
    r"multiple\s+choice\s+questions|mcqs?|questions)\s*$",
    re.IGNORECASE,
)
_TABLE_MIN_LINES = 3
_TABLE_NUMERIC_LINE_RATIO = 0.5


@dataclass
class ExtractionOutput:
    pages: list[PageExtraction]
    blocks: list[ContentBlock]


class _ZoneTracker:
    """Sticky page-zone classification (Step 10). FRONT_MATTER until the
    first CHAPTER/UNIT heading; APPENDIX/INDEX are sticky once triggered
    (both conventionally appear once, near the end of a book).

    APPENDIX/INDEX detection is deliberately gated on _seen_main_content:
    a front-matter table of contents routinely *lists* an "Appendix" or
    "Index" entry among its chapter listing (e.g. "Appendix: Ventricles,
    Cranial Nerves and Arteries  193") — without this gate, that single TOC
    line would flip the zone for the rest of the book before any real
    content had even started.
    """

    def __init__(self) -> None:
        self.current = PageClassification.FRONT_MATTER
        self._seen_main_content = False

    def observe(self, heading: DetectedHeading, block_text: str) -> None:
        if heading.level in (HeadingLevel.CHAPTER, HeadingLevel.UNIT_SECTION):
            if not self._seen_main_content:
                self.current = PageClassification.MAIN_CONTENT
                self._seen_main_content = True

        if not self._seen_main_content:
            return

        stripped = block_text.strip()
        if _INDEX_HEADING_RE.match(stripped):
            self.current = PageClassification.INDEX
        elif _APPENDIX_RE.search(stripped) and len(stripped) < 60:
            self.current = PageClassification.APPENDIX


def _compute_body_font_size(document: fitz.Document) -> float:
    """Weighted-by-character-count mode of line font sizes across the whole
    document — the reference "this is what body text looks like" baseline
    that classify_font_heading() compares every line against. A first pass
    over the already-open document; no second file read."""
    weighted: Counter[int] = Counter()
    for page in document:
        try:
            page_dict = page.get_text("dict")
        except Exception:  # noqa: BLE001 - a single unreadable page must not abort the baseline pass
            continue
        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                text = "".join(span.get("text", "") for span in spans)
                if not text.strip():
                    continue
                size = max((span.get("size", 0.0) for span in spans), default=0.0)
                weighted[round(size)] += len(text)
    if not weighted:
        return 0.0
    return float(weighted.most_common(1)[0][0])


def _block_text_and_font(pdict_block: dict) -> tuple[str, float]:
    lines_text: list[str] = []
    max_size = 0.0
    for line in pdict_block.get("lines", []):
        spans = line.get("spans", [])
        line_text = "".join(span.get("text", "") for span in spans)
        if line_text.strip():
            lines_text.append(line_text)
        for span in spans:
            size = span.get("size", 0.0)
            if size > max_size:
                max_size = size
    return "\n".join(lines_text).strip(), max_size


def _looks_like_table(text: str) -> bool:
    """Coarse, informational-only signal (Deviations: full table-structure
    extraction via PyMuPDF's find_tables() was deliberately not built this
    phase — see AI-7B report)."""
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < _TABLE_MIN_LINES:
        return False
    numeric_lines = sum(1 for line in lines if len(re.findall(r"\d+(?:\.\d+)?", line)) >= 2)
    return (numeric_lines / len(lines)) >= _TABLE_NUMERIC_LINE_RATIO


def _page_is_questions(cleaned_text: str) -> bool:
    for line in cleaned_text.splitlines()[:8]:
        if line.strip() and _QUESTIONS_HEADING_RE.match(line.strip()):
            return True
    return False


def _classify_extraction(
    page: fitz.Page, raw_text: str, extraction_threw: bool
) -> ExtractionStatus:
    if extraction_threw:
        return ExtractionStatus.EXTRACTION_FAILED

    char_count = len(raw_text.strip())
    try:
        has_images = len(page.get_images(full=True)) > 0
    except Exception:  # noqa: BLE001 - image inspection is a best-effort signal, not required
        has_images = False

    if char_count < _MIN_CHARS_TEXT_OK:
        return ExtractionStatus.POSSIBLE_SCAN if has_images else ExtractionStatus.TEXT_SPARSE
    return ExtractionStatus.TEXT_OK


def _is_folio_block(pdict_block: dict, page_height: float) -> bool:
    """A block that is *only* a bare number sitting in the top/bottom folio
    zone — a running page number, never body content."""
    if not page_height:
        return False
    block_text, _ = _block_text_and_font(pdict_block)
    stripped = block_text.strip()
    if not _PRINTED_PAGE_NUMBER_RE.match(stripped):
        return False
    bbox = pdict_block.get("bbox")
    if not bbox:
        return False
    y0, y1 = bbox[1], bbox[3]
    return y1 < page_height * _PAGE_NUMBER_ZONE_RATIO or y0 > page_height * (
        1 - _PAGE_NUMBER_ZONE_RATIO
    )


def _detect_printed_page_number(dict_blocks: list[dict], page_height: float) -> int | None:
    for pdict_block in dict_blocks:
        if _is_folio_block(pdict_block, page_height):
            block_text, _ = _block_text_and_font(pdict_block)
            return int(block_text.strip())
    return None


_RUNNING_HEADER_MIN_PAGE_OCCURRENCES = 5
_RUNNING_HEADER_MIN_PAGE_FRACTION = 0.05


def _demote_running_headers(blocks: list[ContentBlock], total_pages: int) -> list[ContentBlock]:
    """A HEADING/SUBHEADING-tier block whose exact text repeats across many
    distinct pages is a running header/footer (e.g. the book's title, or
    the current chapter's title, printed on every page) — not real
    document structure. TextCleaner's own repeated-header stripping (see
    ingestion/cleaning/text_cleaner.py) only touches plain per-page text; it
    never sees the font-based block stream built here, so the same
    "repeats across most pages -> not real content" signal is re-applied at
    this layer. Demoted blocks are kept as plain body text, not dropped —
    only their (mis)classification as a heading is removed.
    """
    pages_by_text: dict[str, set[int]] = {}
    for block in blocks:
        if block.heading is not None and block.heading.level in (
            HeadingLevel.HEADING,
            HeadingLevel.SUBHEADING,
        ):
            pages_by_text.setdefault(block.text, set()).add(block.pdf_page_number)

    threshold = max(
        _RUNNING_HEADER_MIN_PAGE_OCCURRENCES, int(total_pages * _RUNNING_HEADER_MIN_PAGE_FRACTION)
    )
    running_header_texts = {
        text for text, pages in pages_by_text.items() if len(pages) >= threshold
    }
    if not running_header_texts:
        return blocks

    return [
        block.model_copy(update={"heading": None}) if block.text in running_header_texts else block
        for block in blocks
    ]


def _merge_chapter_title_continuations(blocks: list[ContentBlock]) -> list[ContentBlock]:
    """Real textbooks frequently print a chapter number and its title as
    two typographically separate lines ("CHAPTER 9" then, in a different
    style, "Heart Muscle; The Heart as a Pump..." right below it) — two
    separate PyMuPDF blocks. Without this merge, the CHAPTER heading would
    capture an empty title and the title line would be misread as a new
    section heading instead. Merges only within the same page, and only
    when the CHAPTER block captured no title of its own."""
    merged: list[ContentBlock] = []
    index = 0
    while index < len(blocks):
        block = blocks[index]
        has_next = index + 1 < len(blocks)
        if (
            block.heading is not None
            and block.heading.level is HeadingLevel.CHAPTER
            and not block.heading.text
            and has_next
        ):
            next_block = blocks[index + 1]
            if (
                next_block.heading is not None
                and next_block.heading.level is HeadingLevel.HEADING
                and next_block.pdf_page_number == block.pdf_page_number
            ):
                combined_heading = block.heading.model_copy(
                    update={"text": next_block.text.strip()}
                )
                combined_block = block.model_copy(
                    update={
                        "text": f"{block.text} {next_block.text}".strip(),
                        "heading": combined_heading,
                    }
                )
                merged.append(combined_block)
                index += 2
                continue
        merged.append(block)
        index += 1
    return merged


class TextbookPageExtractor:
    """Opens a PDF's raw bytes (already read through DocumentStorage by the
    caller — this class never touches the filesystem itself) and produces
    both a per-page record set (for pages.jsonl) and a flat, structure-
    tagged ContentBlock stream (the chunker's input).

    Runs in three passes over the already-open document (no second file
    read): (1) a cheap font-size baseline pass, (2) per-page block
    collection with heading *candidates* only — no structure state applied
    yet, so a chapter-title-continuation merge can run across the whole
    block stream first — then (3) a single ordered pass applying
    StructureTracker/zone classification for real. A page-level extraction
    failure is caught and recorded as EXTRACTION_FAILED for that page only;
    a whole-document problem (encrypted, unopenable) raises immediately.
    """

    def extract(self, document_id: UUID, content: bytes) -> ExtractionOutput:
        try:
            document = fitz.open(stream=content, filetype="pdf")
        except Exception as exc:
            raise DocumentParseError(filename=str(document_id), reason=str(exc)) from exc

        try:
            return self._extract(document_id, document)
        finally:
            document.close()

    def _extract(self, document_id: UUID, document: fitz.Document) -> ExtractionOutput:
        if document.needs_pass and not document.authenticate(""):
            raise EncryptedDocumentError(document_id=document_id)

        body_font_size = _compute_body_font_size(document)

        raw_pages: list[ParsedPage] = []
        extraction_failed_pages: set[int] = set()
        for index, page in enumerate(document):
            pdf_page_number = index + 1
            try:
                raw_text = page.get_text("text")
            except Exception:  # noqa: BLE001 - one bad page must not abort the whole document
                logger.warning(
                    "page_extraction_failed document_id=%s pdf_page_number=%s",
                    document_id,
                    pdf_page_number,
                )
                raw_text = ""
                extraction_failed_pages.add(pdf_page_number)
            raw_pages.append(ParsedPage(page_number=pdf_page_number, text=raw_text))

        cleaned_pages = TextCleaner().clean_pages(raw_pages) if raw_pages else []
        cleaned_by_page = {page.page_number: page.text for page in cleaned_pages}

        raw_blocks: list[ContentBlock] = []
        printed_page_by_page: dict[int, int | None] = {}
        for index, page in enumerate(document):
            pdf_page_number = index + 1
            page_blocks, printed_page_number = self._collect_page_blocks(
                document_id=document_id,
                page=page,
                pdf_page_number=pdf_page_number,
                body_font_size=body_font_size,
            )
            printed_page_by_page[pdf_page_number] = printed_page_number
            raw_blocks.extend(page_blocks)

        raw_blocks = _demote_running_headers(raw_blocks, total_pages=len(raw_pages))
        merged_blocks = _merge_chapter_title_continuations(raw_blocks)
        blocks_by_page = {
            page_number: list(group)
            for page_number, group in groupby(merged_blocks, key=lambda b: b.pdf_page_number)
        }

        tracker = StructureTracker()
        zone = _ZoneTracker()
        blocks: list[ContentBlock] = []
        headings_by_page: dict[int, list[DetectedHeading]] = {}
        structure_after_by_page: dict[int, StructureState] = {}
        classification_by_page: dict[int, PageClassification] = {}

        for index in range(len(raw_pages)):
            pdf_page_number = index + 1
            cleaned_text = cleaned_by_page.get(pdf_page_number, "")
            is_questions_page = _page_is_questions(cleaned_text)
            page_classification = (
                PageClassification.QUESTIONS if is_questions_page else zone.current
            )
            page_headings: list[DetectedHeading] = []

            for block in blocks_by_page.get(pdf_page_number, []):
                if block.heading is not None:
                    page_headings.append(block.heading)
                    zone.observe(block.heading, block.text)
                    tracker.apply(block.heading)
                    page_classification = (
                        PageClassification.QUESTIONS if is_questions_page else zone.current
                    )
                blocks.append(block.model_copy(update={"page_classification": page_classification}))

            headings_by_page[pdf_page_number] = page_headings
            structure_after_by_page[pdf_page_number] = tracker.state
            classification_by_page[pdf_page_number] = page_classification

        pages: list[PageExtraction] = []
        for index, page in enumerate(document):
            pdf_page_number = index + 1
            raw_text = raw_pages[index].text
            cleaned_text = cleaned_by_page.get(pdf_page_number, "")
            extraction_status = _classify_extraction(
                page, raw_text, pdf_page_number in extraction_failed_pages
            )
            pages.append(
                PageExtraction(
                    document_id=document_id,
                    pdf_page_number=pdf_page_number,
                    printed_page_number=printed_page_by_page.get(pdf_page_number),
                    raw_text=raw_text,
                    cleaned_text=cleaned_text,
                    extraction_status=extraction_status,
                    classification=classification_by_page.get(
                        pdf_page_number, PageClassification.UNKNOWN
                    ),
                    headings=headings_by_page.get(pdf_page_number, []),
                    structure_after=structure_after_by_page.get(pdf_page_number, StructureState()),
                )
            )

        return ExtractionOutput(pages=pages, blocks=blocks)

    def _collect_page_blocks(
        self,
        *,
        document_id: UUID,
        page: fitz.Page,
        pdf_page_number: int,
        body_font_size: float,
    ) -> tuple[list[ContentBlock], int | None]:
        try:
            page_dict = page.get_text("dict")
        except Exception:  # noqa: BLE001 - structure detection is best-effort per page
            logger.warning(
                "page_structure_extraction_failed document_id=%s pdf_page_number=%s",
                document_id,
                pdf_page_number,
            )
            return [], None

        page_height = page.rect.height if page.rect else 0.0
        dict_blocks = [b for b in page_dict.get("blocks", []) if b.get("type") == 0]
        printed_page_number = _detect_printed_page_number(dict_blocks, page_height)

        blocks: list[ContentBlock] = []
        for pdict_block in dict_blocks:
            if _is_folio_block(pdict_block, page_height):
                continue
            block_text, max_font = _block_text_and_font(pdict_block)
            stripped = block_text.strip()
            if not stripped:
                continue

            heading = match_keyword_heading(block_text)
            if heading is None:
                font_level = classify_font_heading(block_text, max_font, body_font_size)
                if font_level is not None:
                    # Collapse internal newlines/whitespace runs for heading
                    # *text* specifically (e.g. a wrapped subheading block)
                    # — section_title/subsection_title are stored metadata,
                    # not flowing body content, so they should read as one
                    # clean line. ContentBlock.text itself is left as-is;
                    # newlines are harmless in body content the chunker
                    # joins as a unit regardless.
                    heading = DetectedHeading(level=font_level, text=" ".join(stripped.split()))

            blocks.append(
                ContentBlock(
                    pdf_page_number=pdf_page_number,
                    printed_page_number=printed_page_number,
                    text=stripped,
                    heading=heading,
                    is_table=_looks_like_table(block_text),
                    is_figure_caption=bool(_CAPTION_RE.match(stripped)),
                    page_classification=PageClassification.UNKNOWN,  # stamped for real in _extract
                )
            )

        return blocks, printed_page_number
