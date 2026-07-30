from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.prompting.models.prompt import PromptResponse


class GenerationParameters(BaseModel):
    """Optional per-request overrides of GenerationService/OpenAIProvider's
    configured defaults. Any field left unset falls back to Settings-derived
    configuration."""

    model_config = ConfigDict(extra="forbid")

    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_output_tokens: int | None = Field(default=None, gt=0)
    timeout_seconds: float | None = Field(default=None, gt=0)


class GenerationRequest(BaseModel):
    """Input to GenerationService.generate(). Consumes an already-completed
    PromptResponse from AI-5 — this service never calls PromptService or
    RetrievalService itself."""

    model_config = ConfigDict(extra="forbid")

    prompt_response: PromptResponse
    model: str | None = None
    parameters: GenerationParameters = Field(default_factory=GenerationParameters)
    request_id: str = Field(default_factory=lambda: str(uuid4()))
