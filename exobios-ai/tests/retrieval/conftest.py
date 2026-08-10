import pytest

from app.retrieval.models.retrieval import RetrievedChunk, SearchResult
from tests.embeddings.conftest import (  # noqa: F401 - re-exported fixtures/helpers
    FakeOpenAIClient,
    FakeQdrantClient,
    fake_openai_client,
    fake_qdrant_client,
    make_chunk,
    make_document_metadata,
    make_scored_point,
    make_search_payload,
)


class FakeEmbeddingProvider:
    """Stands in for EmbeddingProvider without touching OpenAI."""

    def __init__(self, dimensions: int = 4, fail_with: Exception | None = None) -> None:
        self._dimensions = dimensions
        self.fail_with = fail_with
        self.embedded_texts: list[str] = []

    @property
    def model(self) -> str:
        return "fake-embedding-model"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_text(self, text: str) -> list[float]:
        if self.fail_with is not None:
            raise self.fail_with
        self.embedded_texts.append(text)
        return [float(len(text))] * self._dimensions

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


class FakeRetriever:
    """Stands in for Retriever, recording calls without a real VectorStore."""

    def __init__(
        self, result: SearchResult | None = None, fail_with: Exception | None = None
    ) -> None:
        self.result = result if result is not None else SearchResult(chunks=[])
        self.fail_with = fail_with
        self.calls: list[tuple[list[float], int, float | None, dict | None]] = []
        self.health_result = True

    def search(self, query_vector, top_k, min_score=None, filters=None) -> SearchResult:
        if self.fail_with is not None:
            raise self.fail_with
        self.calls.append((query_vector, top_k, min_score, filters))
        return self.result

    def health(self) -> bool:
        return self.health_result


class FakeReranker:
    """Stands in for Reranker, recording calls and just truncating input."""

    def __init__(self, fail_with: Exception | None = None) -> None:
        self.fail_with = fail_with
        self.calls: list[tuple[list, int]] = []

    def rerank(self, chunks: list[RetrievedChunk], max_results: int) -> list[RetrievedChunk]:
        if self.fail_with is not None:
            raise self.fail_with
        self.calls.append((chunks, max_results))
        return chunks[:max_results]


@pytest.fixture
def fake_embedding_provider() -> FakeEmbeddingProvider:
    return FakeEmbeddingProvider()


def make_retrieved_chunk(**overrides) -> RetrievedChunk:
    document = overrides.pop("document", None) or make_document_metadata()
    chunk = overrides.pop("chunk", None) or make_chunk(document.id)
    defaults = {
        "document_id": document.id,
        "chunk_id": chunk.id,
        "score": 0.9,
        "text": chunk.text,
        "page_number": chunk.metadata.page_number,
        "section_title": chunk.metadata.section_title,
        "document_type": document.document_type,
        "filename": document.filename,
        "language": document.language,
        "tags": document.tags,
        "version": document.version,
        "source": document.source,
    }
    defaults.update(overrides)
    return RetrievedChunk(**defaults)
