from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.generation.models.usage import TokenUsage
from app.schemas.analyze import RiskLevel

# RiskAssessment.level reuses RiskLevel (LOW/MEDIUM/HIGH/CRITICAL) from
# app.schemas.analyze rather than redefining an identical enum — it's the
# same clinical concept AI-1 already models, and StrEnum values match the
# spec exactly.


class LikelihoodLevel(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class RedFlagSeverity(StrEnum):
    WARNING = "WARNING"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"


class ActionPriority(StrEnum):
    ROUTINE = "ROUTINE"
    SOON = "SOON"
    URGENT = "URGENT"
    IMMEDIATE = "IMMEDIATE"


class PossibleCondition(BaseModel):
    """A *possible* condition suggested by the evidence — never a confirmed
    diagnosis. Both the schema and the prompts (see templates/) preserve
    that distinction; ResponseValidator additionally screens the free-text
    fields for confirmed-diagnosis wording."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    likelihood: LikelihoodLevel
    reasoning: str
    supporting_citation_numbers: list[int] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: RiskLevel
    reasoning: str = Field(min_length=1)
    requires_immediate_escalation: bool
    supporting_citation_numbers: list[int] = Field(default_factory=list)


class GeneratedRedFlag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1)
    severity: RedFlagSeverity
    action: str = Field(min_length=1)
    supporting_citation_numbers: list[int] = Field(default_factory=list)


class RecommendedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str = Field(min_length=1)
    priority: ActionPriority
    reasoning: str
    supporting_citation_numbers: list[int] = Field(default_factory=list)


class CitationReference(BaseModel):
    """Trusted citation metadata. Populated exclusively by ResponseValidator
    from the prompt's RetrievedContext — never from LLM output. page_number
    is the only optional field (chunks from non-paginated formats like DOCX
    have none); every other field always exists on a retrieved chunk."""

    model_config = ConfigDict(extra="forbid")

    citation_number: int
    document_id: UUID
    chunk_id: UUID
    filename: str
    page_number: int | None = None
    source: str


class ClinicalGenerationDraft(BaseModel):
    """The exact schema requested from the LLM via structured output
    (`text_format=` on OpenAI's Responses API). `citations` here is a
    manifest of citation *numbers* the model claims to have used — never
    full CitationReference objects, since the model must not be trusted to
    invent document_id/chunk_id/filename/source. ResponseValidator turns
    this into a validated ClinicalGenerationOutput.
    """

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    possible_conditions: list[PossibleCondition] = Field(default_factory=list)
    risk_assessment: RiskAssessment
    red_flags: list[GeneratedRedFlag] = Field(default_factory=list)
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    citations: list[int] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ClinicalGenerationOutput(BaseModel):
    """The validated clinical draft: identical to ClinicalGenerationDraft
    except `citations` has been resolved into trusted CitationReference
    objects by ResponseValidator. This — never a raw ClinicalGenerationDraft
    — is what GenerationResult carries."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    possible_conditions: list[PossibleCondition] = Field(default_factory=list)
    risk_assessment: RiskAssessment
    red_flags: list[GeneratedRedFlag] = Field(default_factory=list)
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    citations: list[CitationReference] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class RawGenerationResponse(BaseModel):
    """LLMProvider.generate_structured()'s return value: a successfully
    parsed clinical draft plus provider-level metadata, before business
    validation. Refusals, empty responses, and malformed output never reach
    this type — they're raised as exceptions by the provider instead."""

    model_config = ConfigDict(extra="forbid")

    draft: ClinicalGenerationDraft
    model: str
    usage: TokenUsage
    finish_reason: str
    provider_request_id: str | None = None
    latency_ms: float = Field(ge=0)


class GenerationMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    usage: TokenUsage
    latency_ms: float = Field(ge=0)
    finish_reason: str
    provider_request_id: str | None = None
    generated_at: datetime


class GenerationResult(BaseModel):
    """GenerationService's final, provider-independent output."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    output: ClinicalGenerationOutput
    # Convenience accessor — identical to output.citations, exposed at the
    # top level so callers don't need to drill into `output` for the thing
    # they'll most often want (e.g. rendering source links).
    resolved_citations: list[CitationReference]
    metadata: GenerationMetadata
