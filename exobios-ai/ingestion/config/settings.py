"""
define all versions
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # openai_api_key: str
    zeroshot_classification_token_hf: str
    supabase_url: str
    supabase_key: str
    # S3 upload calls are currently commented out in loaders/loader.py, so
    # these are optional for local development — only required once S3
    # upload is re-enabled for production document storage.
    s3_bucket_name_parsed_doc: str | None = None
    s3_bucket_name_raw_doc: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_default_region: str | None = None
    chunk_max_tokens: int = 400
    ingestion_version: str = "ingestion_2026_07_31" 
    openai_embedding_model: str = "text-embedding-3-small"
    openai_api_key: str | None = None
    chunk_max_tokens: int = 400
    qdrant_url: str
    collection_name: str
    
    embedding_model: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()