import requests

from config.settings import settings
from core.exceptions import RetrievalException


class EmbeddingService:
    """Wraps the HF-hosted embedding model. Must stay identical to whatever
    embedded the Qdrant corpus at ingestion time (all-MiniLM-L6-v2, 384-dim),
    or query vectors and stored vectors won't live in the same space."""

    def __init__(self):
        self.url = settings.embedding.embed_url
        self.headers = {"Authorization": f"Bearer {settings.embedding.hf_token}"}

    def embed(self, text: str) -> list[float]:
        try:
            response = requests.post(self.url, headers=self.headers, json={"inputs": text}, timeout=30)
            response.raise_for_status()
            vector = response.json()
        except Exception as e:
            raise RetrievalException(f"embedding request failed: {e}")

        if not isinstance(vector, list) or not vector or isinstance(vector[0], list):
            raise RetrievalException(f"unexpected embedding response shape: {type(vector)}")
        return vector


embedding_service = EmbeddingService()