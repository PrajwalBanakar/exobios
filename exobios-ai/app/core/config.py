from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="exobios-ai", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    enable_api_docs: bool = Field(default=True, alias="ENABLE_API_DOCS")

    # Required: the service must refuse to start without a real key. This must
    # match the backend's `app.ai.api-key` / `AI_API_KEY` value exactly.
    ai_api_key: str = Field(alias="AI_API_KEY")

    # Required: no embeddings can be generated without it.
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    embedding_batch_size: int = Field(default=100, alias="EMBEDDING_BATCH_SIZE")

    # Local Qdrant (see docker-compose.yml) has no auth by default, so the
    # API key is optional unlike the required secrets above.
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="exobios_chunks", alias="QDRANT_COLLECTION")

    retrieval_top_k: int = Field(default=20, alias="RETRIEVAL_TOP_K")
    min_similarity_score: float = Field(default=0.0, alias="MIN_SIMILARITY_SCORE")
    max_returned_chunks: int = Field(default=10, alias="MAX_RETURNED_CHUNKS")

    max_prompt_tokens: int = Field(default=4000, alias="MAX_PROMPT_TOKENS")
    max_context_tokens: int = Field(default=2000, alias="MAX_CONTEXT_TOKENS")
    reserved_response_tokens: int = Field(default=500, alias="RESERVED_RESPONSE_TOKENS")
    default_prompt_template: str = Field(default="diagnosis", alias="DEFAULT_PROMPT_TEMPLATE")

    # Reuses openai_api_key above — no separate LLM API key setting.
    llm_model: str = Field(default="gpt-4.1-mini", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.2, ge=0.0, le=2.0, alias="LLM_TEMPERATURE")
    llm_max_output_tokens: int = Field(default=1500, gt=0, alias="LLM_MAX_OUTPUT_TOKENS")
    llm_timeout_seconds: float = Field(default=30.0, gt=0, alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=2, ge=0, le=10, alias="LLM_MAX_RETRIES")
    # Optional: the prompt-budget check in GenerationService only runs when
    # this is configured, since not every deployment wants to hardcode a
    # specific model's context window here.
    llm_context_window: int | None = Field(default=None, gt=0, alias="LLM_CONTEXT_WINDOW")

    @field_validator("ai_api_key", "openai_api_key")
    @classmethod
    def api_key_must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("API key fields must be set to a non-empty value")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
