from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DocumentType(StrEnum):
    PDF = "PDF"
    DOCX = "DOCX"
    TXT = "TXT"
    MARKDOWN = "MARKDOWN"


class DocumentStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Adding a new format only requires a new entry here plus a parser registered
# in ParserRegistry — no existing code needs to change (open/closed).
_EXTENSION_TO_TYPE: dict[str, DocumentType] = {
    ".pdf": DocumentType.PDF,
    ".docx": DocumentType.DOCX,
    ".txt": DocumentType.TXT,
    ".md": DocumentType.MARKDOWN,
    ".markdown": DocumentType.MARKDOWN,
}


def detect_document_type(filename: str) -> DocumentType | None:
    """Resolve a document type from a filename's extension, or None if unknown."""
    return _EXTENSION_TO_TYPE.get(Path(filename).suffix.lower())


class DocumentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    filename: str
    original_path: str
    document_type: DocumentType
    source: str
    version: str = "1.0"
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    checksum: str
    status: DocumentStatus = DocumentStatus.PENDING
    page_count: int = 0
    chunk_count: int = 0
    tags: list[str] = Field(default_factory=list)
    language: str | None = None
