from abc import ABC, abstractmethod

from app.retrieval.models.retrieval import RetrievedChunk


class Reranker(ABC):
    """Common interface every result-ranking strategy implements. Swapping
    the baseline score sort for a Cross-Encoder, Cohere Rerank, or Voyage
    Rerank means adding a new Reranker subclass — RetrievalService's
    contract doesn't change."""

    @abstractmethod
    def rerank(self, chunks: list[RetrievedChunk], max_results: int) -> list[RetrievedChunk]: ...


class ScoreReranker(Reranker):
    """Baseline strategy: drop duplicate chunk ids (keeping the
    highest-scoring occurrence), sort by similarity score descending, then
    limit to `max_results`."""

    def rerank(self, chunks: list[RetrievedChunk], max_results: int) -> list[RetrievedChunk]:
        best_by_chunk_id: dict = {}
        for chunk in chunks:
            existing = best_by_chunk_id.get(chunk.chunk_id)
            if existing is None or chunk.score > existing.score:
                best_by_chunk_id[chunk.chunk_id] = chunk

        ranked = sorted(best_by_chunk_id.values(), key=lambda c: c.score, reverse=True)
        return ranked[:max_results]
