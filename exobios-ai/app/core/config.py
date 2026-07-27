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

    @field_validator("ai_api_key")
    @classmethod
    def api_key_must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("AI_API_KEY must be set to a non-empty value")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
