from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DocumentType(StrEnum):
    PDF = "PDF"
    DOCX = "DOCX"
    TXT = "TXT"
    MARKDOWN = "MARKDOWN"


class DocumentStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Subject(StrEnum):
    """Textbook subject taxonomy. A StrEnum (rather than a free-text field)
    catches typos at registration time; adding a new subject later — e.g.
    PATHOLOGY, PHARMACOLOGY, MEDICINE, PEDIATRICS, OBSTETRICS — is a one-line
    addition here, not a schema redesign."""

    ANATOMY = "ANATOMY"
    PHYSIOLOGY = "PHYSIOLOGY"
    BIOCHEMISTRY = "BIOCHEMISTRY"


class ApprovalStatus(StrEnum):
    """Whether a registered document has been cleared for use. Distinct from
    DocumentStatus (ingestion_status): a document can be APPROVED and still
    PENDING ingestion, or ingested (COMPLETED) yet later REJECTED and pulled
    from future retrieval — the two lifecycles are independent."""

    PENDING = "PENDING"
    APPROVED_FOR_POC = "APPROVED_FOR_POC"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# Adding a new format only requires a new entry here plus a parser registered
# in ParserRegistry — no existing code needs to change (open/closed).
_EXTENSION_TO_TYPE: dict[str, DocumentType] = {
    ".pdf": DocumentType.PDF,
    ".docx": DocumentType.DOCX,
    ".txt": DocumentType.TXT,
    ".md": DocumentType.MARKDOWN,
    ".markdown": DocumentType.MARKDOWN,
}


def detect_document_type(filename: str) -> DocumentType | None:
    """Resolve a document type from a filename's extension, or None if unknown."""
    return _EXTENSION_TO_TYPE.get(Path(filename).suffix.lower())


class DocumentMetadata(BaseModel):
    """Document-level metadata. `id` is the document_id; `filename` already
    serves as source_filename (the name the file arrived under); `status`
    already serves as ingestion_status (see DocumentStatus) — the ingestion
    pipeline's existing fields are reused rather than duplicated wherever
    they already mean what a textbook registry needs.

    The book-specific fields below (title through allow_image_display) are
    all optional: IngestionService's own construction of DocumentMetadata
    (for non-textbook documents ingested directly, e.g. the IMNCI PDF) never
    sets them, and they default to None/PENDING accordingly. They're
    populated by the registration workflow (scripts/register_document.py)
    for textbooks specifically.
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    filename: str
    original_path: str
    document_type: DocumentType
    source: str
    version: str = "1.0"
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    checksum: str
    status: DocumentStatus = DocumentStatus.PENDING
    page_count: int = 0
    chunk_count: int = 0
    tags: list[str] = Field(default_factory=list)
    language: str | None = None

    # ── Textbook registry metadata (AI-7A) ───────────────────────────────
    title: str | None = None
    subject: Subject | None = None
    author: str | None = None
    publisher: str | None = None
    edition: str | None = None
    publication_year: int | None = None
    # Logical, portable key into DocumentStorage (e.g. "physiology/book.pdf")
    # — distinct from original_path, which is the ingestion pipeline's own
    # provenance field and may hold an arbitrary local filesystem path.
    storage_key: str | None = None
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # ── Future fields (nullable, no behavior attached yet) ───────────────
    # Only the two fields the client specifically flagged as near-term
    # (diagram display planning) — see AI-7A deliverables for why the rest
    # of the previously-proposed future fields (clinical_priority,
    # jurisdiction, effective_date, superseded_by, allow_text_quote) were
    # left out for now rather than added speculatively.
    copyright_status: str | None = None
    allow_image_display: bool | None = None
