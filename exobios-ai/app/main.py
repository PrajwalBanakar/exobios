from fastapi import FastAPI

from api.routes import analyze, health
from core.exceptions import (
    AppException,
    handle_app_exception,
    handle_unexpected_exception,
)
from core.logging_config import setup_logging
from core.observability import setup_observability
from middleware.request_context import RequestContextMiddleware

setup_logging()
setup_observability()


def create_app() -> FastAPI:
    app = FastAPI(title="exobios-ai")

    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(AppException, handle_app_exception)
    # Catch-all so a bug outside the AppException hierarchy still returns a
    # structured, non-leaking 500 instead of Starlette's bare default error.
    app.add_exception_handler(Exception, handle_unexpected_exception)

    app.include_router(analyze.router)
    app.include_router(health.router)

    return app


app = create_app()