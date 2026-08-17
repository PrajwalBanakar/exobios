import requests

from config.settings import settings
from core.exceptions import RetrievalException
from core.retry import retry_with_backoff


def _is_retryable(e: Exception) -> bool:
    if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.ChunkedEncodingError)):
        return True
    if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
        return e.response.status_code in (429, 500, 502, 503, 504)
    return False


class EmbeddingService:
    """Wraps the HF-hosted embedding model. Must stay identical to whatever
    embedded the Qdrant corpus at ingestion time (all-MiniLM-L6-v2, 384-dim),
    or query vectors and stored vectors won't live in the same space."""

    def __init__(self):
        self.url = settings.embedding.embed_url
        self.headers = {"Authorization": f"Bearer {settings.embedding.hf_token}"}

    def embed(self, text: str) -> list[float]:
        def _call():
            response = requests.post(self.url, headers=self.headers, json={"inputs": text}, timeout=30)
            response.raise_for_status()
            return response.json()

        try:
            vector = retry_with_backoff(_call, is_retryable=_is_retryable, op_name="embedding request")
        except Exception as e:
            raise RetrievalException(f"embedding request failed: {e}") from e

        if not isinstance(vector, list) or not vector or isinstance(vector[0], list):
            raise RetrievalException(f"unexpected embedding response shape: {type(vector)}")
        return vector


embedding_service = EmbeddingService()