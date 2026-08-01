from google import genai
from google.genai import types

from app.embeddings.exceptions import EmbeddingGenerationError
from app.embeddings.providers.base import EmbeddingProvider

# gemini-embedding-001 defaults to 3072 dimensions but supports truncation to
# smaller sizes via output_dimensionality (Matryoshka representation
# learning) — 768 keeps Qdrant vectors small and searches fast for dev/demo
# use without a meaningful quality loss versus the full size.
_DEFAULT_DIMENSIONS = 768


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Generates embeddings via the Gemini API. Free-tier alternative to
    OpenAIEmbeddingProvider for local dev/demo use — implements the same
    EmbeddingProvider interface, so nothing upstream (EmbeddingService,
    IngestionService, RetrievalService) needs to know which provider is
    configured.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-001",
        batch_size: int = 100,
        dimensions: int = _DEFAULT_DIMENSIONS,
        client: genai.Client | None = None,
    ) -> None:
        self._model = model
        self._batch_size = batch_size
        self._dimensions = dimensions
        self._client = client or genai.Client(api_key=api_key)

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_text(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            try:
                response = self._client.models.embed_content(
                    model=self._model,
                    contents=batch,
                    config=types.EmbedContentConfig(output_dimensionality=self._dimensions),
                )
            except Exception as exc:
                raise EmbeddingGenerationError(reason=str(exc)) from exc
            vectors.extend(embedding.values for embedding in response.embeddings)

        return vectors
