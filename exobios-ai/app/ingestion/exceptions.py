from uuid import UUID

from app.core.exceptions import AppError


class IngestionError(AppError):
    """Base class for all document ingestion errors."""


class UnsupportedDocumentType(IngestionError):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        super().__init__(
            status_code=400,
            code="UNSUPPORTED_DOCUMENT_TYPE",
            message=f"Unsupported document type for file '{filename}'",
        )


class DuplicateDocument(IngestionError):
    def __init__(self, checksum: str, existing_document_id: UUID) -> None:
        self.checksum = checksum
        self.existing_document_id = existing_document_id
        super().__init__(
            status_code=409,
            code="DUPLICATE_DOCUMENT",
            message=(
                f"Document with checksum '{checksum}' was already ingested "
                f"as {existing_document_id}"
            ),
        )


class DocumentParseError(IngestionError):
    def __init__(self, filename: str, reason: str) -> None:
        self.filename = filename
        self.reason = reason
        super().__init__(
            status_code=422,
            code="DOCUMENT_PARSE_ERROR",
            message=f"Failed to parse document '{filename}': {reason}",
        )


class ChunkingError(IngestionError):
    def __init__(self, reason: str, document_id: UUID | None = None) -> None:
        self.document_id = document_id
        self.reason = reason
        target = f" document {document_id}" if document_id else ""
        super().__init__(
            status_code=422,
            code="CHUNKING_ERROR",
            message=f"Failed to chunk{target}: {reason}",
        )
