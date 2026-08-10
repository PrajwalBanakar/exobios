from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.ingestion.models.document import Subject


class ExtractionStatus(StrEnum):
    """Per-page text-extraction quality. POSSIBLE_SCAN and EXTRACTION_FAILED
    are both signals that a page may need OCR in a future phase — this phase
    only detects and reports that, it never runs OCR itself."""

    TEXT_OK = "TEXT_OK"
    TEXT_SPARSE = "TEXT_SPARSE"
    POSSIBLE_SCAN = "POSSIBLE_SCAN"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


class PageClassification(StrEnum):
    """Coarse zone a page belongs to, so future retrieval can down-rank or
    exclude non-main-content without deleting anything now."""

    FRONT_MATTER = "FRONT_MATTER"
    MAIN_CONTENT = "MAIN_CONTENT"
    APPENDIX = "APPENDIX"
    QUESTIONS = "QUESTIONS"
    INDEX = "INDEX"
    UNKNOWN = "UNKNOWN"


class HeadingLevel(StrEnum):
    """Structural level of a detected heading block. CHAPTER/UNIT_SECTION
    are keyword-pattern matches (high confidence); HEADING/SUBHEADING are
    font-size-relative heuristics (lower confidence, best-effort)."""

    UNIT_SECTION = "UNIT_SECTION"
    CHAPTER = "CHAPTER"
    HEADING = "HEADING"
    SUBHEADING = "SUBHEADING"


class DetectedHeading(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: HeadingLevel
    text: str
    number: str | None = (
        None  # raw captured token, e.g. "9", "III", "THREE" — never converted/normalized
    )


class StructureState(BaseModel):
    """Running structural position. All fields nullable: a page before the
    first detected chapter has every field None rather than a guessed value."""

    model_config = ConfigDict(extra="forbid")

    unit_or_section: str | None = None
    chapter_number: str | None = None
    chapter_title: str | None = None
    section_title: str | None = None
    subsection_title: str | None = None


class ContentBlock(BaseModel):
    """One paragraph-or-heading-sized unit of page content, in reading
    order — the chunker's input. Roughly one PyMuPDF text block; a detected
    table is instead exactly one ContentBlock per table (or one per
    row-group if the table itself exceeds the chunk token ceiling)."""

    model_config = ConfigDict(extra="forbid")

    pdf_page_number: int
    printed_page_number: int | None
    text: str
    heading: DetectedHeading | None = None
    is_table: bool = False
    is_figure_caption: bool = False
    page_classification: PageClassification


class PageExtraction(BaseModel):
    """One record per physical PDF page — written to pages.jsonl."""

    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    pdf_page_number: int
    printed_page_number: int | None = None
    raw_text: str
    cleaned_text: str
    extraction_status: ExtractionStatus
    classification: PageClassification
    headings: list[DetectedHeading] = Field(default_factory=list)
    structure_after: StructureState


class TextbookChunkMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    subject: Subject | None
    title: str | None
    edition: str | None
    unit_or_section: str | None
    chapter_number: str | None
    chapter_title: str | None
    section_title: str | None
    subsection_title: str | None
    pdf_page_start: int
    pdf_page_end: int
    printed_page_start: int | None
    printed_page_end: int | None
    chunk_index: int
    token_count: int
    page_classification: PageClassification
    figure_references: list[str] = Field(default_factory=list)


class TextbookChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    metadata: TextbookChunkMetadata


class ProcessingSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    title: str | None
    subject: Subject | None
    total_pdf_pages: int
    pages_with_text: int
    sparse_pages: int
    possible_scanned_pages: int
    extraction_failed_pages: int
    chapters_detected: int
    chunks_created: int
    min_tokens: int
    max_tokens: int
    mean_tokens: float
    median_tokens: float
    p95_tokens: float
    oversized_chunks: int
    undersized_chunks: int
    generated_at: datetime
