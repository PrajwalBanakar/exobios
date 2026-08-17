import secrets

from fastapi import Header

from config.settings import settings
from core.exceptions import AuthenticationError
from core.rate_limit import RateLimiter

_analyze_limiter = RateLimiter(
    max_requests=settings.rate_limit.requests,
    window_seconds=settings.rate_limit.window_seconds,
)


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    # Header(default=None) instead of Header(...): a missing key must map to
    # the same 401 AuthenticationError as a wrong key, not to FastAPI's 422
    # "missing header" validation error — callers shouldn't see two different
    # status codes for what is, from their perspective, one failure mode
    # ("not authenticated").
    if x_api_key is None or not secrets.compare_digest(x_api_key, settings.ai_api_key):
        raise AuthenticationError("invalid or missing X-Api-Key")


def check_rate_limit(x_api_key: str | None = Header(default=None)) -> None:
    """Runs AFTER verify_api_key in the route's dependency list — see
    analyze.py — so an invalid key is rejected (401) before ever touching
    the limiter. Keyed by the caller's API key, not patient/assessment
    identifiers: rate limiting protects the service from call volume by
    *caller*, and a patient-keyed limit would both leak nothing useful
    (there's one shared caller today) and let one high-volume legitimate
    caller starve unrelated patients' requests of their own budget instead
    of sharing one budget per authenticated caller as intended."""
    if not settings.rate_limit.enabled:
        return
    _analyze_limiter.check(x_api_key or "unknown")
