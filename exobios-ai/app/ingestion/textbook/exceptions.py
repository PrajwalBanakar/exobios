from uuid import UUID

from app.ingestion.exceptions import IngestionError


class TextbookProcessingError(IngestionError):
    """Base class for textbook extraction/chunking errors — a sibling of the
    existing ingestion exceptions (DocumentParseError, ChunkingError, ...),
    reusing the same IngestionError base rather than inventing a parallel
    hierarchy."""


class DocumentNotRegisteredError(TextbookProcessingError):
    def __init__(self, document_id: UUID) -> None:
        self.document_id = document_id
        super().__init__(
            status_code=404,
            code="DOCUMENT_NOT_REGISTERED",
            message=f"No registered document found for id {document_id}",
        )


class DocumentMissingStorageKeyError(TextbookProcessingError):
    def __init__(self, document_id: UUID) -> None:
        self.document_id = document_id
        super().__init__(
            status_code=422,
            code="DOCUMENT_MISSING_STORAGE_KEY",
            message=f"Document {document_id} has no storage_key — was it registered via "
            "scripts/register_document.py?",
        )


class UnsupportedTextbookFormatError(TextbookProcessingError):
    def __init__(self, document_id: UUID, document_type: str) -> None:
        self.document_id = document_id
        self.document_type = document_type
        super().__init__(
            status_code=422,
            code="UNSUPPORTED_TEXTBOOK_FORMAT",
            message=f"Document {document_id} has type {document_type}; textbook extraction "
            "currently supports PDF only",
        )


class EncryptedDocumentError(TextbookProcessingError):
    def __init__(self, document_id: UUID) -> None:
        self.document_id = document_id
        super().__init__(
            status_code=422,
            code="ENCRYPTED_DOCUMENT",
            message=f"Document {document_id} is password-protected and could not be opened",
        )
