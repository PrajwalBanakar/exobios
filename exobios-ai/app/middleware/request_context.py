import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from core.logging_config import request_id_ctx

logger = logging.getLogger("app.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Reuse the caller's correlation id (Spring Boot backend) when present,
        # so logs on both sides of that hop share one id; mint a fresh one
        # otherwise. This is the single id used for both the response header
        # and every log line for the request — nothing downstream should
        # override it (see api/routes/analyze.py, which used to).
        incoming = request.headers.get("x-request-id") or request.headers.get("x-correlation-id")
        request_id = incoming or str(uuid.uuid4())
        request_id_ctx.set(request_id)
        start = time.time()

        response = await call_next(request)

        duration_ms = round((time.time() - start) * 1000, 1)
        logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
        response.headers["X-Request-Id"] = request_id
        return response