import secrets

from fastapi import Header

from config.settings import settings
from core.exceptions import AuthenticationError


def verify_api_key(x_api_key: str = Header(...)) -> None:
    if not secrets.compare_digest(x_api_key, settings.ai_api_key):
        raise AuthenticationError("invalid X-Api-Key")