from app.core.exceptions import AppError


class StorageError(AppError):
    """Base class for all document storage errors."""


class DocumentNotFoundError(StorageError):
    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(
            status_code=404,
            code="DOCUMENT_NOT_FOUND",
            message=f"No document found for storage key '{key}'",
        )


class InvalidStorageKeyError(StorageError):
    """Raised for any key that is blank, absolute, or resolves outside the
    storage root — the single choke point that prevents path traversal
    (e.g. '../../secret.env') regardless of which DocumentStorage caller
    constructed the key."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(
            status_code=400,
            code="INVALID_STORAGE_KEY",
            message=f"Storage key '{key}' is not a valid, root-confined key",
        )
