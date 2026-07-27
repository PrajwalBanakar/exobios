import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes.analyze import router as analyze_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.middleware.request_context import RequestContextMiddleware
from app.schemas.errors import ErrorDetail, ErrorResponse

logger = logging.getLogger("app.main")


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    docs_url = "/docs" if settings.enable_api_docs else None
    redoc_url = "/redoc" if settings.enable_api_docs else None
    openapi_url = "/openapi.json" if settings.enable_api_docs else None

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    app.add_middleware(RequestContextMiddleware)

    app.include_router(health_router)
    app.include_router(analyze_router)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        body = ErrorResponse(
            request_id=_request_id(request),
            error=ErrorDetail(code=exc.code, message=exc.message),
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        body = ErrorResponse(
            request_id=_request_id(request),
            error=ErrorDetail(code="VALIDATION_ERROR", message="Request validation failed"),
        )
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(Exception)
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error while processing request")
        body = ErrorResponse(
            request_id=_request_id(request),
            error=ErrorDetail(code="INTERNAL_ERROR", message="An internal error occurred"),
        )
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
