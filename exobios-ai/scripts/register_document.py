"""Register a textbook (or list registered textbooks) in the Exobios AI
document registry — AI-7A's developer workflow for the 5-PDF POC. Registers
metadata only; it does not parse, chunk, embed, or touch Qdrant.

Run from exobios-ai/, after the file is already placed under
DOCUMENT_STORAGE_ROOT (see data/README.md):

    python scripts/register_document.py register \\
        --file data/source_documents/physiology/book.pdf \\
        --subject physiology \\
        --title "Guyton and Hall Textbook of Medical Physiology" \\
        --author "John E. Hall" \\
        --edition "14th" \\
        --publisher "Elsevier" \\
        --publication-year 2020 \\
        --approval-status approved_for_poc

    python scripts/register_document.py list
    python scripts/register_document.py list --subject physiology
"""

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.ingestion.exceptions import DuplicateDocument, UnsupportedDocumentType
from app.ingestion.models.document import (
    ApprovalStatus,
    DocumentMetadata,
    DocumentStatus,
    Subject,
    detect_document_type,
)
from app.ingestion.registry.interface import DocumentRegistry
from app.ingestion.registry.sqlite_registry import SQLiteDocumentRegistry
from app.storage.exceptions import InvalidStorageKeyError
from app.storage.local_storage import LocalDocumentStorage

_SUBJECT_CHOICES = [s.value.lower() for s in Subject]
_APPROVAL_CHOICES = [s.value.lower() for s in ApprovalStatus]


class RegistrationError(Exception):
    """Preconditions this script itself checks, distinct from errors raised
    by DocumentRegistry/DocumentStorage."""


def register_document(
    *,
    file_path: Path,
    storage: LocalDocumentStorage,
    registry: DocumentRegistry,
    subject: Subject,
    title: str,
    author: str | None = None,
    publisher: str | None = None,
    edition: str | None = None,
    publication_year: int | None = None,
    language: str = "en",
    source: str = "manual-upload",
    tags: list[str] | None = None,
    approval_status: ApprovalStatus = ApprovalStatus.PENDING,
    copyright_status: str | None = None,
    allow_image_display: bool | None = None,
) -> DocumentMetadata:
    """Core registration logic, independent of argparse/stdout so tests can
    call it directly. Computes the checksum and storage_key itself — callers
    never supply document_id, checksum, created_at, or updated_at."""
    if not file_path.is_file():
        raise RegistrationError(f"File not found: {file_path}")

    document_type = detect_document_type(file_path.name)
    if document_type is None:
        raise UnsupportedDocumentType(filename=file_path.name)

    try:
        storage_key = file_path.resolve().relative_to(storage.root).as_posix()
    except ValueError as exc:
        raise RegistrationError(
            f"'{file_path}' is not inside DOCUMENT_STORAGE_ROOT ({storage.root}); "
            "move it under data/source_documents/<subject>/ first"
        ) from exc

    if not storage.exists(storage_key):
        # Should be unreachable given the is_file() check above — confirms
        # the file is genuinely readable *through* DocumentStorage, not just
        # present on disk under some coincidentally-matching path.
        raise RegistrationError(f"'{storage_key}' is not readable through DocumentStorage")

    checksum = hashlib.sha256(storage.read(storage_key)).hexdigest()

    # Checked here rather than left to whichever DocumentRegistry backend is
    # injected: InMemoryDocumentRegistry (used in tests, and available for
    # lightweight local use) does not itself enforce checksum uniqueness —
    # today only IngestionService does, by checking before it registers.
    # Mirroring that same check here keeps "the same textbook registered
    # twice is rejected, not silently duplicated" true regardless of backend.
    existing = registry.find_by_checksum(checksum)
    if existing is not None:
        raise DuplicateDocument(checksum=checksum, existing_document_id=existing.id)

    metadata = DocumentMetadata(
        filename=file_path.name,
        original_path=str(file_path.resolve()),
        document_type=document_type,
        source=source,
        checksum=checksum,
        status=DocumentStatus.PENDING,
        tags=tags or [],
        language=language,
        title=title,
        subject=subject,
        author=author,
        publisher=publisher,
        edition=edition,
        publication_year=publication_year,
        storage_key=storage_key,
        approval_status=approval_status,
        copyright_status=copyright_status,
        allow_image_display=allow_image_display,
    )

    registry.register(metadata)
    return metadata


def list_documents(
    registry: DocumentRegistry,
    *,
    subject: Subject | None = None,
    approval_status: ApprovalStatus | None = None,
) -> list[DocumentMetadata]:
    return registry.list_all(subject=subject, approval_status=approval_status)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Register or list textbooks in the Exobios AI document registry."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_parser = subparsers.add_parser(
        "register", help="Register a document already placed under DOCUMENT_STORAGE_ROOT"
    )
    register_parser.add_argument(
        "--file", required=True, type=Path, help="e.g. data/source_documents/physiology/book.pdf"
    )
    register_parser.add_argument("--subject", required=True, choices=_SUBJECT_CHOICES)
    register_parser.add_argument("--title", required=True)
    register_parser.add_argument("--author", default=None)
    register_parser.add_argument("--publisher", default=None)
    register_parser.add_argument("--edition", default=None)
    register_parser.add_argument("--publication-year", type=int, default=None)
    register_parser.add_argument("--language", default="en")
    register_parser.add_argument("--source", default="manual-upload")
    register_parser.add_argument("--tags", default="", help="Comma-separated, e.g. who,pediatrics")
    register_parser.add_argument(
        "--approval-status",
        default=ApprovalStatus.PENDING.value.lower(),
        choices=_APPROVAL_CHOICES,
    )
    register_parser.add_argument("--copyright-status", default=None)
    register_parser.add_argument(
        "--allow-image-display", action=argparse.BooleanOptionalAction, default=None
    )

    list_parser = subparsers.add_parser("list", help="List registered documents")
    list_parser.add_argument("--subject", default=None, choices=_SUBJECT_CHOICES)
    list_parser.add_argument("--approval-status", default=None, choices=_APPROVAL_CHOICES)

    return parser


def _print_table(documents: list[DocumentMetadata]) -> None:
    headers = ("document_id", "subject", "title", "edition", "approval", "ingestion", "storage_key")
    rows = [
        (
            str(doc.id),
            doc.subject.value if doc.subject else "-",
            doc.title or doc.filename,
            doc.edition or "-",
            doc.approval_status.value,
            doc.status.value,
            doc.storage_key or "-",
        )
        for doc in documents
    ]
    widths = [max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(headers)]

    def fmt(row: tuple[str, ...]) -> str:
        return "  ".join(cell.ljust(width) for cell, width in zip(row, widths, strict=True))

    print(fmt(headers))
    print(fmt(tuple("-" * width for width in widths)))
    for row in rows:
        print(fmt(row))


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    settings = get_settings()
    storage = LocalDocumentStorage(root=settings.document_storage_root_path)
    registry = SQLiteDocumentRegistry(db_path=settings.document_registry_db_path_resolved)

    if args.command == "register":
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        try:
            metadata = register_document(
                file_path=args.file,
                storage=storage,
                registry=registry,
                subject=Subject(args.subject.upper()),
                title=args.title,
                author=args.author,
                publisher=args.publisher,
                edition=args.edition,
                publication_year=args.publication_year,
                language=args.language,
                source=args.source,
                tags=tags,
                approval_status=ApprovalStatus(args.approval_status.upper()),
                copyright_status=args.copyright_status,
                allow_image_display=args.allow_image_display,
            )
        except DuplicateDocument as exc:
            print(
                f"Already registered: checksum {exc.checksum} matches "
                f"existing document {exc.existing_document_id}",
                file=sys.stderr,
            )
            return 1
        except (RegistrationError, UnsupportedDocumentType, InvalidStorageKeyError) as exc:
            print(f"Registration failed: {exc}", file=sys.stderr)
            return 1

        print(
            f"Registered '{metadata.title}' ({metadata.subject.value}) as document_id={metadata.id}"
        )
        print(f"  storage_key: {metadata.storage_key}")
        print(f"  checksum:    {metadata.checksum}")
        return 0

    if args.command == "list":
        documents = list_documents(
            registry,
            subject=Subject(args.subject.upper()) if args.subject else None,
            approval_status=(
                ApprovalStatus(args.approval_status.upper()) if args.approval_status else None
            ),
        )
        if not documents:
            print("No documents registered yet.")
            return 0
        _print_table(documents)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
