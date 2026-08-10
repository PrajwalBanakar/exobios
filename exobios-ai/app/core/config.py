from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# app/core/config.py -> app/core -> app -> exobios-ai. Anchoring resolution
# here (rather than leaving relative paths to resolve against whatever the
# process's current working directory happens to be) means DOCUMENT_STORAGE_ROOT
# and DOCUMENT_REGISTRY_DB_PATH behave the same whether the app is started from
# exobios-ai/, from a script in scripts/, or by a test runner from anywhere else.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


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

    # Exactly one of these two must be set (see api_key_provider_is_configured
    # below). GEMINI_API_KEY is a free-tier alternative for local dev/demo
    # use — when set, the embeddings and generation factories wire up Gemini
    # providers instead of OpenAI's, with no other code changes required.
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
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

    # ── Document storage + registry (AI-7A) ──────────────────────────────
    # Relative paths are resolved against _PROJECT_ROOT (see
    # document_storage_root_path / document_registry_db_path_resolved below),
    # not the process's current working directory.
    document_storage_root: str = Field(
        default="./data/source_documents", alias="DOCUMENT_STORAGE_ROOT"
    )
    document_registry_db_path: str = Field(
        default="./data/document_registry.db", alias="DOCUMENT_REGISTRY_DB_PATH"
    )
    document_extracted_root: str = Field(
        default="./data/extracted", alias="DOCUMENT_EXTRACTED_ROOT"
    )
    document_processed_root: str = Field(
        default="./data/processed", alias="DOCUMENT_PROCESSED_ROOT"
    )

    @property
    def document_storage_root_path(self) -> Path:
        path = Path(self.document_storage_root)
        return path if path.is_absolute() else (_PROJECT_ROOT / path).resolve()

    @property
    def document_registry_db_path_resolved(self) -> Path:
        path = Path(self.document_registry_db_path)
        return path if path.is_absolute() else (_PROJECT_ROOT / path).resolve()

    @property
    def document_extracted_root_path(self) -> Path:
        path = Path(self.document_extracted_root)
        return path if path.is_absolute() else (_PROJECT_ROOT / path).resolve()

    @property
    def document_processed_root_path(self) -> Path:
        path = Path(self.document_processed_root)
        return path if path.is_absolute() else (_PROJECT_ROOT / path).resolve()

    # ── Textbook chunking (AI-7B) ─────────────────────────────────────────
    textbook_chunk_target_tokens: int = Field(
        default=650, gt=0, alias="TEXTBOOK_CHUNK_TARGET_TOKENS"
    )
    textbook_chunk_max_tokens: int = Field(default=800, gt=0, alias="TEXTBOOK_CHUNK_MAX_TOKENS")
    textbook_chunk_overlap_tokens: int = Field(
        default=100, ge=0, alias="TEXTBOOK_CHUNK_OVERLAP_TOKENS"
    )
    textbook_min_chunk_tokens: int = Field(default=20, ge=0, alias="TEXTBOOK_MIN_CHUNK_TOKENS")

    # ── Textbook RAG (AI-7C) ──────────────────────────────────────────────
    # A separate collection from `qdrant_collection` (used by the existing
    # IMNCI clinical-guideline demo) — deliberately isolated so textbook
    # ingestion can never leak chunks into, or be searched by, that
    # existing working pipeline. One collection for every subject (not one
    # per subject) — subject is payload metadata, filtered at query time.
    qdrant_textbook_collection: str = Field(
        default="exobios_knowledge", alias="QDRANT_TEXTBOOK_COLLECTION"
    )
    # Plain string (not the GroundingMode enum) so config.py stays free of
    # imports from app.textbook_qa — validated against the known set below;
    # consumers convert via GroundingMode(settings.knowledge_grounding_mode).
    # Only STRICT is actually implemented in this phase (see PART 11 of the
    # AI-7C+ spec) — AUGMENTED/GENERAL are accepted here so the setting/enum
    # shape doesn't need to change later, but selecting them today raises.
    knowledge_grounding_mode: str = Field(default="STRICT", alias="KNOWLEDGE_GROUNDING_MODE")
    # Chosen empirically against real retrieval score distributions — see
    # the AI-7C completion report for the observed valid-vs-unrelated-query
    # score gap this value was picked from.
    textbook_min_retrieval_score: float = Field(
        default=0.5, ge=0.0, le=1.0, alias="TEXTBOOK_MIN_RETRIEVAL_SCORE"
    )

    @field_validator("knowledge_grounding_mode")
    @classmethod
    def grounding_mode_must_be_known(cls, value: str) -> str:
        allowed = {"STRICT", "AUGMENTED", "GENERAL"}
        normalized = value.strip().upper()
        if normalized not in allowed:
            raise ValueError(f"KNOWLEDGE_GROUNDING_MODE must be one of {sorted(allowed)}")
        return normalized

    @field_validator("ai_api_key")
    @classmethod
    def api_key_must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("API key fields must be set to a non-empty value")
        return value

    @field_validator("openai_api_key", "gemini_api_key", "llm_context_window", mode="before")
    @classmethod
    def blank_env_string_becomes_unset(cls, value: object) -> object:
        # A literal `KEY=` line in .env parses as "" (not "unset"), which
        # would otherwise fail int-parsing (llm_context_window) or read as a
        # falsy-but-present secret. Treat a blank string as not-configured
        # so a template .env with unfilled optional lines still loads.
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def one_embedding_and_generation_provider_key_is_configured(self) -> "Settings":
        if not self.openai_api_key and not self.gemini_api_key:
            raise ValueError("Set either OPENAI_API_KEY or GEMINI_API_KEY")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
