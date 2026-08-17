from enum import StrEnum
from pydantic import BaseModel
from typing import List


class DocumentStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentMetadata(BaseModel):
    document_id: str
    document_title: str
    complaint_category: str
    applicable_roles: List[str]
    file_location: str
    # SHA-256 of the source file's raw bytes. document_id is derived from
    # this (see loaders/loader.py), so re-ingesting identical file content
    # always produces the same document_id/chunk ids and safely upserts in
    # place instead of duplicating; different content for the "same" file
    # produces a new document_id, i.e. is treated as a new document version.
    content_hash: str
    # A document is only COMPLETED once parsing, chunking, embedding, AND
    # the Qdrant upsert have all succeeded (see loaders/loader.py::run()).
    # FAILED carries a short, sanitized reason in error_message — never a
    # full traceback or anything that could contain a secret/token.
    status: DocumentStatus = DocumentStatus.PENDING
    error_message: str | None = None
    # Versioning/supersession foundation — see the 2026-08 audit's Priority
    # 8 and the matching migration for the full rationale. logical_document_key
    # is currently the source filename's stem (a default heuristic set by
    # loaders/loader.py, not a hard product decision). is_active is flipped
    # to False on a PRIOR version once a NEW version of the same
    # logical_document_key finishes ingestion successfully — never before,
    # so a failed re-ingestion never deactivates a working prior version.
    logical_document_key: str | None = None
    is_active: bool = True
