from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class QdrantSettings(BaseModel):
    url: str = "http://localhost:6333"
    collection_name: str = "corpus"


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


class LLMSettings(BaseModel):
    groq_api_key: str
    model: str = "llama-3.3-70b-versatile"
    max_output_tokens: int = 2048
    temperature: float = 0.2


class MongoSettings(BaseModel):
    uri: str
    db_name: str = "exobios"
    assessments_collection: str = "assessments"


class LangSmithSettings(BaseModel):
    api_key: str = "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"
    project: str = "exobios-ai"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    ai_api_key: str

    qdrant: QdrantSettings = QdrantSettings()
    embedding: EmbeddingSettings
    reranker: RerankerSettings
    llm: LLMSettings
    mongo: MongoSettings
    langsmith: LangSmithSettings = LangSmithSettings()


settings = Settings()