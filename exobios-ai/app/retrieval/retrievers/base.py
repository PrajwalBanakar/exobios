from abc import ABC, abstractmethod

from app.retrieval.models.retrieval import SearchResult


class Retriever(ABC):
    """Common interface every candidate-retrieval strategy implements.
    Swapping the backing search technique (semantic, BM25, hybrid, ...)
    means adding a new Retriever subclass — RetrievalService depends only
    on this interface."""

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
        min_score: float | None = None,
        filters: dict[str, object] | None = None,
    ) -> SearchResult: ...

    @abstractmethod
    def health(self) -> bool: ...
