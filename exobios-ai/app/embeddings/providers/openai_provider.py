from openai import OpenAI

from app.embeddings.exceptions import EmbeddingGenerationError
from app.embeddings.providers.base import EmbeddingProvider

# text-embedding-3-large is included for completeness even though it isn't
# the configured default; ada-002 remains for callers on the legacy model.
_MODEL_DIMENSIONS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}
_DEFAULT_DIMENSIONS = 1536


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Generates embeddings via the OpenAI embeddings API, batching requests
    to stay within the API's per-request input limits."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        batch_size: int = 100,
        client: OpenAI | None = None,
    ) -> None:
        self._model = model
        self._batch_size = batch_size
        self._client = client or OpenAI(api_key=api_key)

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return _MODEL_DIMENSIONS.get(self._model, _DEFAULT_DIMENSIONS)

    def embed_text(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            try:
                response = self._client.embeddings.create(model=self._model, input=batch)
            except Exception as exc:
                raise EmbeddingGenerationError(reason=str(exc)) from exc
            vectors.extend(item.embedding for item in response.data)

        return vectors
