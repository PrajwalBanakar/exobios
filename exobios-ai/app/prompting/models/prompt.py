from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.ingestion.models.document import DocumentType
from app.retrieval.models.retrieval import RetrievedChunk, SearchRequest
from app.schemas.analyze import ComplaintCategory, SymptomSummary, VitalsSummary


class PromptTemplateName(StrEnum):
    DIAGNOSIS = "diagnosis"
    TRIAGE = "triage"
    RECOMMENDATION = "recommendation"


class PromptSectionName(StrEnum):
    SYSTEM_INSTRUCTIONS = "system_instructions"
    PATIENT_INFORMATION = "patient_information"
    VITAL_SIGNS = "vital_signs"
    SYMPTOMS = "symptoms"
    RETRIEVED_KNOWLEDGE = "retrieved_knowledge"
    CLINICAL_RULES_PLACEHOLDER = "clinical_rules_placeholder"
    OUTPUT_FORMAT = "output_format"
    CITATION_INSTRUCTIONS = "citation_instructions"


class PatientContext(BaseModel):
    """Patient-assessment data relevant to prompt construction.

    Deliberately independent of AiRequest's backend JSON-contract concerns
    (camelCase aliases, Jackson null-omission) — this is the prompting
    layer's own representation, reusing AiRequest's data-shaped sub-models
    (SymptomSummary, VitalsSummary, ComplaintCategory) rather than duplicating
    them.
    """

    model_config = ConfigDict(extra="forbid")

    assessment_id: UUID
    patient_id: UUID
    patient_complaint: str | None = None
    complaint_category: ComplaintCategory | None = None
    symptoms: list[SymptomSummary] = Field(default_factory=list)
    vitals: VitalsSummary | None = None
    past_illnesses: str | None = None
    current_medications: str | None = None
    allergies: str | None = None


class CitedChunk(BaseModel):
    """A RetrievedChunk annotated with its citation number. Numbers are
    assigned once by ContextFormatter, in relevance order, and never
    renumbered afterward (including after token-budget trimming) — so a
    citation's number always reflects its original relevance rank."""

    model_config = ConfigDict(extra="forbid")

    citation_number: int
    chunk: RetrievedChunk


class DocumentGroup(BaseModel):
    """All cited chunks originating from one source document, in relevance
    order, preserving source attribution for the rendered prompt."""

    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    filename: str
    document_type: DocumentType
    source: str
    citations: list[CitedChunk]


class RetrievedContext(BaseModel):
    """ContextFormatter's output: deduplicated, relevance-sorted, numbered,
    and grouped by source document."""

    model_config = ConfigDict(extra="forbid")

    groups: list[DocumentGroup]
    total_chunks: int
    discarded_chunk_count: int = 0


class PromptContext(BaseModel):
    """The full render context PromptBuilder assembles a prompt from."""

    model_config = ConfigDict(extra="forbid")

    patient: PatientContext
    retrieved_context: RetrievedContext


class PromptSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: PromptSectionName
    content: str
    token_count: int


class PromptTemplate(BaseModel):
    """Identifies which template file produced a prompt."""

    model_config = ConfigDict(extra="forbid")

    name: PromptTemplateName
    file_name: str


class PromptMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assessment_id: UUID
    template: PromptTemplateName
    created_at: datetime
    section_names: list[PromptSectionName]
    citation_count: int


class PromptStatistics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt_tokens: int
    context_tokens: int
    reserved_response_tokens: int
    max_prompt_tokens: int
    retrieved_chunk_count: int
    included_chunk_count: int
    discarded_chunk_count: int


class PromptRequest(BaseModel):
    """Input to PromptService.build_prompt()."""

    model_config = ConfigDict(extra="forbid")

    patient: PatientContext
    search_request: SearchRequest
    template: PromptTemplateName | None = None


class PromptResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str
    sections: list[PromptSection]
    metadata: PromptMetadata
    statistics: PromptStatistics
    # The *trimmed* RetrievedContext actually used to build `prompt` — the
    # same object the RETRIEVED_KNOWLEDGE section's citation numbers were
    # assigned from. Carried here (rather than discarded once rendering is
    # done) so a downstream consumer (AI-6's ResponseValidator) can resolve
    # an LLM's citation numbers against the exact set that appeared in this
    # exact prompt — not the pre-trim set, which could contain citation
    # numbers the model never actually saw.
    retrieved_context: RetrievedContext
