from pydantic import BaseModel, ConfigDict, Field


class TokenUsage(BaseModel):
    """Provider-reported token counts for one generation call. Maps
    directly from OpenAI's Responses API `usage` object (input_tokens,
    output_tokens, total_tokens) — the only place OpenAI-specific token
    accounting is read is openai_provider.py; this model is provider-agnostic.
    """

    model_config = ConfigDict(extra="forbid")

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
