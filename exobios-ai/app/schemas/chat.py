"""Minimal request/response shapes for POST /chat — a dev-only endpoint that
lets the frontend exercise the existing retrieval+generation pipeline
directly (no patient/assessment context, unlike /analyze). Reuses
SupportingCitation so citations look identical to the ones /analyze already
returns."""

from pydantic import BaseModel, Field

from schemas.stages.common import SupportingCitation


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ChatAnswer(BaseModel):
    """Schema the LLM is forced to fill in — see llm_service.generate_structured."""

    answer: str
    grounded: bool


class ChatResponse(BaseModel):
    answer: str
    citations: list[SupportingCitation]
    grounded: bool
