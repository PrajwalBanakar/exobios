from app.core.exceptions import AppError


class RetrievalError(AppError):
    """Top-level failure of RetrievalService.search() — raised for anything
    unexpected that isn't already a more specific AppError (e.g. a
    VectorStoreError/SearchError, which are re-raised as-is)."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=502,
            code="RETRIEVAL_ERROR",
            message=f"Retrieval failed: {reason}",
        )


class SearchError(AppError):
    """Failure of a Retriever's underlying candidate search."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=502,
            code="SEARCH_ERROR",
            message=f"Vector search failed: {reason}",
        )
