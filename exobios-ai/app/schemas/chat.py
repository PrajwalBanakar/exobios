"""Minimal request/response shapes for POST /chat — a dev-only endpoint that
lets the frontend exercise the existing retrieval+generation pipeline
directly (no patient/assessment context, unlike /analyze). Reuses
SupportingCitation so citations look identical to the ones /analyze already
returns."""

from typing import Literal

from pydantic import BaseModel, Field

from schemas.stages.common import SupportingCitation

MAX_HISTORY_TURNS = 12


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    # Prior turns of the same conversation, oldest first. Optional and
    # capped so a stray huge payload can't blow up prompt size.
    history: list[ChatTurn] = Field(default_factory=list, max_length=MAX_HISTORY_TURNS)


class ChatAnswer(BaseModel):
    """Schema the LLM is forced to fill in — see llm_service.generate_structured."""

    answer: str
    grounded: bool


class ChatResponse(BaseModel):
    answer: str
    citations: list[SupportingCitation]
    grounded: bool
