# syntax=docker/dockerfile:1
FROM python:3.13-slim AS base

# uv gives reproducible installs from uv.lock and is much faster than pip.
COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /usr/local/bin/

WORKDIR /app

# Install dependencies first, separately from app code, so the (slow) dependency
# layer is only rebuilt when pyproject.toml/uv.lock change, not on every code edit.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Run as a non-root user, not the container default root.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/.ruff_cache \
    && chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Uses /health, not /health/ready: readiness (Mongo/Qdrant reachability) is
# for an orchestrator's readiness probe deciding whether to route traffic,
# not for Docker's own healthcheck deciding whether to restart the
# container — a transient Mongo/Qdrant blip should not cause Docker to
# restart an otherwise-healthy process.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

# uvicorn handles SIGTERM natively for graceful shutdown (finishes in-flight
# requests, then exits) — no extra signal handling needed. Workers=1: the
# graph/service singletons are constructed once at import time (see
# main.py); running multiple workers would just multiply Mongo/Qdrant/HF
# client connections per instance, so scale via replicas, not --workers,
# unless that eager-singleton-at-import pattern changes.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
