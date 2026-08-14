import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config.settings import settings
from core.exceptions import EmbeddingCompatibilityError
from repositories import assesment
from services.qdrant_service import qdrant_service

router = APIRouter()
logger = logging.getLogger("app.health")

_VERSION = "0.1.0"
# Must match docs/api/ai-service-contract.md's documented /health body
# ("exobios-ai", not "exobios-ai-app") — the Java client doesn't parse this,
# but it's still the cross-team-documented contract and had drifted from it.
_SERVICE_NAME = "exobios-ai"


@router.get("/health")
def health():
    """Liveness only — the process is up and able to handle requests. Does
    NOT check external dependencies; kept cheap and unchanged in shape for
    existing callers. Use /health/ready for a real dependency check."""
    return {"status": "UP", "service": _SERVICE_NAME, "version": _VERSION}


@router.get("/health/ready")
def readiness():
    """Real dependency check — confirms Mongo and Qdrant are actually
    reachable, not just that the process is alive. Intended for use as a
    Kubernetes/ECS readiness probe so traffic isn't routed to an instance
    that can't complete a request. Failures are not raised as 5xx AppExceptions
    (those are for request-handling errors) — this endpoint always returns a
    body describing what it checked, with 503 only when something failed."""
    checks: dict[str, str] = {}
    healthy = True

    try:
        assesment.ping()
        checks["mongo"] = "ok"
    except Exception as e:
        healthy = False
        checks["mongo"] = f"unreachable: {e}"
        logger.warning(f"readiness check failed for mongo: {e}")

    try:
        qdrant_service.client.get_collections()
        checks["qdrant"] = "ok"
    except Exception as e:
        healthy = False
        checks["qdrant"] = f"unreachable: {e}"
        logger.warning(f"readiness check failed for qdrant: {e}")

    # A CONFIRMED mismatch gates readiness — an EmbeddingCompatibilityError
    # means retrieval would silently return meaningless results, not just
    # degraded ones. Missing metadata (legacy corpus) does not gate — see
    # verify_embedding_compatibility's docstring.
    try:
        qdrant_service.verify_embedding_compatibility()
        checks["embedding_compatibility"] = qdrant_service.compatibility_warning or "ok"
    except EmbeddingCompatibilityError as e:
        healthy = False
        checks["embedding_compatibility"] = f"mismatch: {e.message}"
        logger.error(f"readiness check found embedding compatibility mismatch: {e.message}")

    # Informational only — reranking is a quality improvement, not a hard
    # dependency (see services/reranker_service.py), so its state never
    # affects `healthy`/the status code, unlike Mongo/Qdrant above.
    checks["reranker"] = (
        f"enabled (model={settings.reranker.rerank_model})"
        if settings.reranker.enabled
        else "disabled (RERANKER__ENABLED=false)"
    )

    body = {"status": "UP" if healthy else "DOWN", "checks": checks}
    return JSONResponse(status_code=200 if healthy else 503, content=body)
