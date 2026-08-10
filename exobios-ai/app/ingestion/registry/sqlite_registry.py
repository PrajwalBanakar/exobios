import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from app.ingestion.exceptions import DuplicateDocument
from app.ingestion.models.document import (
    ApprovalStatus,
    DocumentMetadata,
    DocumentStatus,
    DocumentType,
    Subject,
)
from app.ingestion.registry.interface import DocumentRegistry

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    original_path TEXT NOT NULL,
    document_type TEXT NOT NULL,
    source TEXT NOT NULL,
    version TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    checksum TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    page_count INTEGER NOT NULL,
    chunk_count INTEGER NOT NULL,
    tags TEXT NOT NULL,
    language TEXT,
    title TEXT,
    subject TEXT,
    author TEXT,
    publisher TEXT,
    edition TEXT,
    publication_year INTEGER,
    storage_key TEXT,
    approval_status TEXT NOT NULL,
    copyright_status TEXT,
    allow_image_display INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_checksum ON documents(checksum);
CREATE INDEX IF NOT EXISTS idx_documents_subject ON documents(subject);
CREATE INDEX IF NOT EXISTS idx_documents_approval_status ON documents(approval_status);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
"""

# Every column except the primary key, in a fixed order shared by INSERT and
# UPDATE so both are generated from one list rather than kept in sync by hand.
_COLUMNS = [
    "id",
    "filename",
    "original_path",
    "document_type",
    "source",
    "version",
    "uploaded_at",
    "checksum",
    "status",
    "page_count",
    "chunk_count",
    "tags",
    "language",
    "title",
    "subject",
    "author",
    "publisher",
    "edition",
    "publication_year",
    "storage_key",
    "approval_status",
    "copyright_status",
    "allow_image_display",
    "created_at",
    "updated_at",
]
_INSERT_SQL = (
    f"INSERT INTO documents ({', '.join(_COLUMNS)}) VALUES ({', '.join(f':{c}' for c in _COLUMNS)})"
)
_UPDATE_SQL = (
    "UPDATE documents SET "
    + ", ".join(f"{c} = :{c}" for c in _COLUMNS if c != "id")
    + " WHERE id = :id"
)


class SQLiteDocumentRegistry(DocumentRegistry):
    """Persistent DocumentRegistry backed by a local SQLite file — the POC's
    persistent alternative to InMemoryDocumentRegistry (which loses every
    registration on process restart).

    Opens a short-lived connection per operation rather than holding one
    open across calls: sqlite3 connections aren't safe to share across
    threads by default, and FastAPI/pytest may run this from a threadpool
    or from many independent tests, so per-call connections are the simplest
    correct option. The cost is irrelevant at this scale (a handful to a few
    hundred rows for the foreseeable POC).

    Migrating to PostgreSQL later means writing a new DocumentRegistry
    implementation (e.g. via psycopg) against this same interface — no
    caller (IngestionService, the registration CLI) needs to change, since
    both depend only on DocumentRegistry, never on this class directly.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connection() as conn:
            conn.executescript(_SCHEMA)

    def register(self, metadata: DocumentMetadata) -> None:
        existing = self.find_by_checksum(metadata.checksum)
        if existing is not None:
            raise DuplicateDocument(checksum=metadata.checksum, existing_document_id=existing.id)

        try:
            with self._connection() as conn:
                conn.execute(_INSERT_SQL, self._to_row(metadata))
        except sqlite3.IntegrityError as exc:
            # Defense in depth against a race between the check above and
            # the insert (e.g. two concurrent registration runs) — the
            # UNIQUE(checksum) constraint is the actual guarantee; this just
            # reports it the same way the pre-check above does.
            existing = self.find_by_checksum(metadata.checksum)
            if existing is not None:
                raise DuplicateDocument(
                    checksum=metadata.checksum, existing_document_id=existing.id
                ) from exc
            raise

    def get(self, document_id: UUID) -> DocumentMetadata | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?", (str(document_id),)
            ).fetchone()
        return self._from_row(row) if row else None

    def find_by_checksum(self, checksum: str) -> DocumentMetadata | None:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM documents WHERE checksum = ?", (checksum,)).fetchone()
        return self._from_row(row) if row else None

    def update(self, metadata: DocumentMetadata) -> None:
        if self.get(metadata.id) is None:
            raise KeyError(f"Document {metadata.id} is not registered")

        updated = metadata.model_copy(update={"updated_at": datetime.now(UTC)})
        with self._connection() as conn:
            conn.execute(_UPDATE_SQL, self._to_row(updated))

    def list_all(
        self,
        *,
        subject: Subject | None = None,
        approval_status: ApprovalStatus | None = None,
        ingestion_status: DocumentStatus | None = None,
    ) -> list[DocumentMetadata]:
        clauses = []
        params: dict[str, str] = {}
        if subject is not None:
            clauses.append("subject = :subject")
            params["subject"] = subject.value
        if approval_status is not None:
            clauses.append("approval_status = :approval_status")
            params["approval_status"] = approval_status.value
        if ingestion_status is not None:
            clauses.append("status = :status")
            params["status"] = ingestion_status.value

        query = "SELECT * FROM documents"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at"

        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._from_row(row) for row in rows]

    def _to_row(self, metadata: DocumentMetadata) -> dict:
        return {
            "id": str(metadata.id),
            "filename": metadata.filename,
            "original_path": metadata.original_path,
            "document_type": metadata.document_type.value,
            "source": metadata.source,
            "version": metadata.version,
            "uploaded_at": metadata.uploaded_at.isoformat(),
            "checksum": metadata.checksum,
            "status": metadata.status.value,
            "page_count": metadata.page_count,
            "chunk_count": metadata.chunk_count,
            "tags": json.dumps(metadata.tags),
            "language": metadata.language,
            "title": metadata.title,
            "subject": metadata.subject.value if metadata.subject else None,
            "author": metadata.author,
            "publisher": metadata.publisher,
            "edition": metadata.edition,
            "publication_year": metadata.publication_year,
            "storage_key": metadata.storage_key,
            "approval_status": metadata.approval_status.value,
            "copyright_status": metadata.copyright_status,
            "allow_image_display": (
                None if metadata.allow_image_display is None else int(metadata.allow_image_display)
            ),
            "created_at": metadata.created_at.isoformat(),
            "updated_at": metadata.updated_at.isoformat(),
        }

    def _from_row(self, row: sqlite3.Row) -> DocumentMetadata:
        return DocumentMetadata(
            id=UUID(row["id"]),
            filename=row["filename"],
            original_path=row["original_path"],
            document_type=DocumentType(row["document_type"]),
            source=row["source"],
            version=row["version"],
            uploaded_at=datetime.fromisoformat(row["uploaded_at"]),
            checksum=row["checksum"],
            status=DocumentStatus(row["status"]),
            page_count=row["page_count"],
            chunk_count=row["chunk_count"],
            tags=json.loads(row["tags"]),
            language=row["language"],
            title=row["title"],
            subject=Subject(row["subject"]) if row["subject"] else None,
            author=row["author"],
            publisher=row["publisher"],
            edition=row["edition"],
            publication_year=row["publication_year"],
            storage_key=row["storage_key"],
            approval_status=ApprovalStatus(row["approval_status"]),
            copyright_status=row["copyright_status"],
            allow_image_display=(
                None if row["allow_image_display"] is None else bool(row["allow_image_display"])
            ),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
