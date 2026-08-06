import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.exceptions")


class AppException(Exception):
    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str = ""):
        self.message = message or self.error_code
        super().__init__(self.message)


class AuthenticationError(AppException):
    status_code = 401
    error_code = "authentication_failed"


class RetrievalException(AppException):
    status_code = 502
    error_code = "retrieval_failed"


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


async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    logger.error(f"{exc.error_code}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )