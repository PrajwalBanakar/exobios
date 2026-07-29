class IngestionError(Exception):
    """Base class for all known/expected ingestion pipeline errors."""
    pass


class DocumentDiscoveryError(IngestionError):
    """Raised when scanning/discovering documents in a folder fails."""

    def __init__(self, folder_path: str, reason: str):
        self.folder_path = folder_path
        self.reason = reason
        super().__init__(f"Failed to discover documents in {folder_path}: {reason}")


class DocumentConversionError(IngestionError):
    """Raised when Docling fails to convert a document."""

    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Failed to convert {file_path}: {reason}")


class MetadataExtractionError(IngestionError):
    """Raised when building DocumentMetadata from a source fails."""

    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Failed to extract metadata for {file_path}: {reason}")


class S3UploadError(IngestionError):
    """Raised when uploading a document to S3 fails."""

    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Failed to upload {file_path} to S3: {reason}")


class DatabasePersistError(IngestionError):
    """Raised when writing to the database fails."""

    def __init__(self, document_id: str, reason: str):
        self.document_id = document_id
        self.reason = reason
        super().__init__(f"Failed to persist document {document_id} to DB: {reason}")