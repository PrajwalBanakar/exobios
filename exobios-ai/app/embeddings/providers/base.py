from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Common interface every embedding backend implements. Swapping models
    (OpenAI, a local model, Voyage AI, Cohere, ...) means adding a new
    EmbeddingProvider subclass — callers depend only on this interface."""

    @property
    @abstractmethod
    def model(self) -> str: ...

    @property
    @abstractmethod
    def dimensions(self) -> int: ...

    @abstractmethod
    def embed_text(self, text: str) -> list[float]: ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
