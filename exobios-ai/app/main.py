from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import analyze, chat, health
from config.settings import settings
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
    # Lets the frontend call /chat directly from the browser (see
    # api/routes/chat.py) to exercise the RAG pipeline. /analyze is never
    # called browser-side (Spring Boot calls it server-to-server), so this
    # only ever needs to list the frontend's own origin(s), never a
    # wildcard — see CORS_ALLOWED_ORIGINS in .env.example.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()],
        allow_methods=["POST", "GET"],
        allow_headers=["Content-Type", "X-Api-Key"],
    )
    app.add_exception_handler(AppException, handle_app_exception)
    # Catch-all so a bug outside the AppException hierarchy still returns a
    # structured, non-leaking 500 instead of Starlette's bare default error.
    app.add_exception_handler(Exception, handle_unexpected_exception)

    app.include_router(analyze.router)
    app.include_router(chat.router)
    app.include_router(health.router)

    return app


app = create_app()