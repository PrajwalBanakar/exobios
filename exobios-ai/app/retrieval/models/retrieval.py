from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.ingestion.models.document import DocumentType, Subject


class RetrievedChunk(BaseModel):
    """A single semantically-matched chunk, denormalized with enough of its
    parent document's metadata to be useful on its own.

    The textbook-specific fields below (subject through page_classification)
    are nullable and populated only for chunks retrieved from the textbook
    knowledge collection (AI-7C) — a clinical-guideline chunk (the IMNCI
    demo path) simply leaves them None. Kept on this same model rather than
    a parallel type so RetrievalService/SemanticRetriever/ContextFormatter
    — none of which have any clinical-specific logic — are reused as-is for
    both use cases.
    """

    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    chunk_id: UUID
    score: float
    text: str
    page_number: int | None
    section_title: str | None
    document_type: DocumentType
    filename: str
    language: str | None
    tags: list[str]
    version: str
    source: str

    # ── Textbook-specific (AI-7C), all nullable ──────────────────────────
    subject: Subject | None = None
    title: str | None = None
    edition: str | None = None
    unit_or_section: str | None = None
    chapter_number: str | None = None
    chapter_title: str | None = None
    subsection_title: str | None = None
    pdf_page_start: int | None = None
    pdf_page_end: int | None = None
    printed_page_start: int | None = None
    printed_page_end: int | None = None
    page_classification: str | None = None


class SearchResult(BaseModel):
    """Raw output of a Retriever — the candidate set before reranking."""

    model_config = ConfigDict(extra="forbid")

    chunks: list[RetrievedChunk]


class SearchRequest(BaseModel):
    """Input to RetrievalService.search(). Overrides are optional — omitted
    fields fall back to the service's configured defaults.

    subject/document_id (AI-7C) are optional metadata filters — when set,
    only chunks whose stored payload matches are considered. Unused by the
    clinical/IMNCI path.
    """

    model_config = ConfigDict(extra="forbid")

    query: str
    top_k: int | None = None
    min_score: float | None = None
    max_returned_chunks: int | None = None
    subject: Subject | None = None
    document_id: UUID | None = None


class SearchResponse(BaseModel):
    """Final output of RetrievalService.search()."""

    model_config = ConfigDict(extra="forbid")

    query: str
    results: list[RetrievedChunk]
    result_count: int
    elapsed_ms: float = Field(ge=0)
