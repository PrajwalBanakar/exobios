from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.ingestion.models.document import Subject


class GroundingMode(StrEnum):
    """Only STRICT is implemented this phase — AUGMENTED/GENERAL exist here
    so the setting/enum shape doesn't need to change when they're built
    later; selecting them today raises UnsupportedGroundingModeError."""

    STRICT = "STRICT"
    AUGMENTED = "AUGMENTED"
    GENERAL = "GENERAL"


class TextbookQuestionRequest(BaseModel):
    """Input to TextbookQAService.answer() — a knowledge Q&A question,
    deliberately independent of PatientContext/clinical assessment models.
    This is a textbook lookup, not a patient case."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    subject: Subject | None = None
    document_id: UUID | None = None
    top_k: int | None = None
    max_returned_chunks: int | None = None


class TextbookAnswerDraft(BaseModel):
    """The exact schema requested from the LLM via structured output.
    `citations` is a manifest of citation *numbers* the model claims to have
    used — never full metadata, since the model must not be trusted to
    invent document/chapter/page details."""

    model_config = ConfigDict(extra="forbid")

    insufficient_evidence: bool
    answer: str = Field(min_length=1)
    citations: list[int] = Field(default_factory=list)


class TextbookCitation(BaseModel):
    """Trusted citation metadata — resolved exclusively from the retrieved
    context the model was actually shown, never from the model's output."""

    model_config = ConfigDict(extra="forbid")

    citation_number: int
    document_id: UUID
    title: str | None
    subject: Subject | None
    edition: str | None
    chapter_number: str | None
    chapter_title: str | None
    section_title: str | None
    pdf_page_start: int | None
    pdf_page_end: int | None
    printed_page_start: int | None
    printed_page_end: int | None


class TextbookAnswerStatus(StrEnum):
    ANSWERED = "ANSWERED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class TextbookAnswerResult(BaseModel):
    """TextbookQAService's final, provider-independent output."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    status: TextbookAnswerStatus
    answer: str | None = None
    citations: list[TextbookCitation] = Field(default_factory=list)
    retrieved_chunk_count: int
    top_score: float | None
    # "retrieval" when refused before an LLM call was made at all (weak
    # scores); "generation" when the model itself returned
    # insufficient_evidence=true after seeing the retrieved evidence.
    refusal_stage: str | None = None
    model: str | None = None
    latency_ms: float | None = None
