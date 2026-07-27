import secrets

from fastapi import Header

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError


async def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-Api-Key")) -> None:
    settings = get_settings()
    if x_api_key is None or not secrets.compare_digest(x_api_key, settings.ai_api_key):
        raise AuthenticationError()
