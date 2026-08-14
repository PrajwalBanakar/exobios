import logging

import requests

from config.settings import settings
from core.retry import retry_with_backoff

logger = logging.getLogger("app.reranker")


def _is_retryable(e: Exception) -> bool:
    if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.ChunkedEncodingError)):
        return True
    if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
        return e.response.status_code in (429, 500, 502, 503, 504)
    return False


class RerankerService:
    """Calls a hosted cross-encoder via HF's sentence-similarity pipeline —
    no local model, matches the "API call, not local inference" constraint.
    On any failure, falls back to the original (pre-rerank) ordering rather
    than raising, since reranking is a quality improvement, not a hard
    dependency for retrieval to function."""

    def __init__(self):
        self.url = settings.reranker.rerank_url
        self.headers = {"Authorization": f"Bearer {settings.reranker.hf_token}"}

    def rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        if not candidates:
            return candidates

        if not settings.reranker.enabled:
            logger.info("reranking disabled (RERANKER__ENABLED=false) — using retrieval fusion order")
            return candidates[:top_k]

        texts = [c["text"] for c in candidates]

        def _call():
            response = requests.post(
                self.url,
                headers=self.headers,
                json={"inputs": {"source_sentence": query, "sentences": texts}},
                timeout=30,
            )
            response.raise_for_status()
            scores = response.json()
            if not isinstance(scores, list) or len(scores) != len(candidates):
                raise ValueError(f"unexpected rerank response shape: {scores}")
            return scores

        try:
            scores = retry_with_backoff(_call, is_retryable=_is_retryable, op_name="reranker request")
        except Exception as e:
            # `degraded_component` is a distinct, greppable field for log-based
            # alerting — this is the one signal that reranking silently
            # stopped improving result order for a request.
            logger.warning(
                f"reranker unavailable, falling back to original order: {e}",
                exc_info=e,
                extra={"degraded_component": "reranker"},
            )
            return candidates[:top_k]

        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return [c for c, _ in ranked[:top_k]]


reranker_service = RerankerService()