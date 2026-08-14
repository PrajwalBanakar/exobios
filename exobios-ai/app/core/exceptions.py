import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from core.logging_config import request_id_ctx

logger = logging.getLogger("app.exceptions")


class AppException(Exception):
    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str = "", headers: dict[str, str] | None = None):
        self.message = message or self.error_code
        self.headers = headers
        super().__init__(self.message)


class AuthenticationError(AppException):
    status_code = 401
    error_code = "authentication_failed"


class RetrievalException(AppException):
    status_code = 502
    error_code = "retrieval_failed"


class EmbeddingCompatibilityError(AppException):
    # Not the caller's fault and not transient upstream flakiness (that's
    # RetrievalException/502) — this means the deployed query-time embedding
    # config doesn't match what the Qdrant corpus was actually ingested
    # with, so similarity search would silently return meaningless results.
    # A genuine server misconfiguration, hence 500.
    status_code = 500
    error_code = "embedding_compatibility_mismatch"


class LLMGenerationException(AppException):
    status_code = 502
    error_code = "llm_generation_failed"


class ValidationFailedException(AppException):
    status_code = 422
    error_code = "output_validation_failed"


class InsufficientEvidenceException(AppException):
    status_code = 200
    error_code = "insufficient_evidence"


class PersistenceException(AppException):
    status_code = 502
    error_code = "persistence_failed"


class RateLimitExceededError(AppException):
    status_code = 429
    error_code = "rate_limit_exceeded"

    def __init__(self, message: str, retry_after_seconds: int):
        super().__init__(message, headers={"Retry-After": str(retry_after_seconds)})


async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    # exc_info picks up exc.__cause__ when raise sites used `raise Foo(...) from e`,
    # so the original traceback (network error, validation error, etc.) is
    # preserved in the log instead of only the flattened message string.
    logger.error(f"{exc.error_code}: {exc.message}", exc_info=exc.__cause__)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message, "request_id": request_id_ctx.get()},
        headers=exc.headers,
    )


async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for anything outside the AppException hierarchy — a bug in a
    graph node, an unhandled pydantic ValidationError building the response,
    etc. Without this, such errors fall through to Starlette's default
    handler: a bare 500 with no error_code/request_id and (depending on
    debug settings) a stack trace leaked to the caller. Logs the full
    traceback server-side; never includes exception details in the response."""
    logger.error(f"unhandled_exception: {exc}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error_code": "internal_error", "message": "internal error", "request_id": request_id_ctx.get()},
    )