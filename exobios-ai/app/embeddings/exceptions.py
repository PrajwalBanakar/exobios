from app.core.exceptions import AppError


class EmbeddingError(AppError):
    """Base class for all embedding-generation and vector-store errors."""


class EmbeddingGenerationError(EmbeddingError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=502,
            code="EMBEDDING_GENERATION_ERROR",
            message=f"Failed to generate embeddings: {reason}",
        )


class VectorStoreError(EmbeddingError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=502,
            code="VECTOR_STORE_ERROR",
            message=f"Vector store operation failed: {reason}",
        )
