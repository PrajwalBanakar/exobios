from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class QdrantSettings(BaseModel):
    url: str = "http://localhost:6333"
    collection_name: str = "corpus"
    # None for local/self-hosted Qdrant (ignored by the client). Required for
    # Qdrant Cloud, which authenticates every request via this header.
    api_key: str | None = None


class EmbeddingSettings(BaseModel):
    hf_token: str
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embed_url: str = (
        "https://router.huggingface.co/hf-inference/models/"
        "sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
    )
    vector_size: int = 384


class RerankerSettings(BaseModel):
    hf_token: str
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_url: str = (
        "https://router.huggingface.co/hf-inference/models/"
        "cross-encoder/ms-marco-MiniLM-L-6-v2"
    )
    # As of the 2026-08 audit, no cross-encoder/text-ranking model has an
    # active hosted-inference provider on HF's router at all (verified live —
    # see docs/ARCHITECTURE.md's Reranker section) — the configured model
    # above 400s on every call. Set RERANKER__ENABLED=false (see .env.example)
    # to skip the guaranteed-failing HTTP round trip rather than pay its
    # latency on every single retrieval call while still falling back
    # correctly. Flip back to true once RERANKER__MODEL/RERANKER__RERANK_URL
    # point at something real, or a self-hosted/local reranker is wired in.
    enabled: bool = True


class LLMSettings(BaseModel):
    groq_api_key: str
    model: str = "llama-3.3-70b-versatile"
    max_output_tokens: int = 2048
    temperature: float = 0.2


class MongoSettings(BaseModel):
    uri: str
    db_name: str = "exobios"
    assessments_collection: str = "assessments"


class RateLimitSettings(BaseModel):
    # In-process only — see core/rate_limit.py's module docstring for why
    # this is a documented limitation, not an oversight, at the current
    # single-instance stage.
    enabled: bool = True
    requests: int = 60
    window_seconds: int = 60


class LangSmithSettings(BaseModel):
    # No default secret here — a real committed LangSmith key was found during
    # the Om-implementation merge and rotated out. Tracing stays opt-in: leave
    # LANGSMITH__API_KEY unset locally and observability.py will not enable it.
    api_key: str = ""
    project: str = "exobios-ai"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    ai_api_key: str
    # Comma-separated origins allowed to call /chat from a browser (see
    # main.py's CORSMiddleware). Defaults to local Vite dev only — set to the
    # real frontend origin(s) in production, e.g.
    # "https://exobios.in,https://www.exobios.in".
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    qdrant: QdrantSettings = QdrantSettings()
    embedding: EmbeddingSettings
    reranker: RerankerSettings
    llm: LLMSettings
    mongo: MongoSettings
    rate_limit: RateLimitSettings = RateLimitSettings()
    langsmith: LangSmithSettings = LangSmithSettings()


settings = Settings()