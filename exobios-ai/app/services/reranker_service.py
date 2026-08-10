import logging

import requests

from config.settings import settings

logger = logging.getLogger("app.reranker")


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

        texts = [c["text"] for c in candidates]
        try:
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
        except Exception as e:
            logger.warning(f"reranker unavailable, falling back to original order: {e}")
            return candidates[:top_k]

        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return [c for c, _ in ranked[:top_k]]


reranker_service = RerankerService()