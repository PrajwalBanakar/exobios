"""
define all versions
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # openai_api_key: str
    zeroshot_classification_token_hf: str
    s3_bucket_name_parsed_doc: str
    s3_bucket_name_raw_doc: str
    supabase_url: str
    supabase_key: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_default_region: str
    chunk_max_tokens: int = 400
    ingestion_version: str = "ingestion_2026_07_31" 
    openai_embedding_model: str = "text-embedding-3-small"
    openai_api_key: str
    chunk_max_tokens: int = 400
    qdrant_url: str
    collection_name: str
    
    embedding_model: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()