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
    # qdrant_url: str = "http://localhost:6333"
    # collection_name: str = "clinical_corpus"
    # embedding_model: str = "text-embedding-3-small"
    # chunk_max_tokens: int = 400
    # tokenizer_model: str = "BAAI/bge-small-en-v1.5"
    # client_files_dir: str = "data/client_files"
    # registry_path: str = "data/registry.json"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()