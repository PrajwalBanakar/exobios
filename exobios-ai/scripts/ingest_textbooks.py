"""Embed AI-7B's already-validated textbook chunks (chunks.jsonl) and store
them in the dedicated textbook Qdrant collection (AI-7C). Never re-extracts
or re-chunks a PDF — reads the existing chunks.jsonl for each document.

Idempotent: re-running without --force skips any document already fully
embedded (Qdrant point count == expected chunk count for that document).

    python scripts/ingest_textbooks.py --document-id <uuid>
    python scripts/ingest_textbooks.py --all-approved-poc
    python scripts/ingest_textbooks.py --all-approved-poc --force
"""

import argparse
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.core.config import get_settings  # noqa: E402
from app.ingestion.exceptions import IngestionError  # noqa: E402
from app.ingestion.models.document import ApprovalStatus  # noqa: E402
from app.ingestion.registry.sqlite_registry import SQLiteDocumentRegistry  # noqa: E402
from app.ingestion.textbook.embedding_ingestion import (  # noqa: E402
    TextbookEmbeddingIngestionResult,
)
from app.ingestion.textbook.factory import (  # noqa: E402
    build_default_textbook_embedding_ingestion_service,
)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Embed AI-7B textbook chunks into the textbook Qdrant collection."
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--document-id", type=UUID, help="Registered document_id to embed")
    target.add_argument(
        "--all-approved-poc",
        action="store_true",
        help="Embed every document with approval_status=APPROVED_FOR_POC",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-embed even if this document already has a full set of vectors stored",
    )
    return parser


def _print_summary(results: list[TextbookEmbeddingIngestionResult]) -> None:
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    header = f"{'Title':<45} {'Chunks':>8} {'Embedded':>10} {'Status':>12}"
    print(header)
    print("-" * len(header))
    for result in results:
        title = (result.title or str(result.document_id))[:45]
        print(
            f"{title:<45} {result.chunks_total:>8} {result.chunks_embedded:>10} "
            f"{result.status.value:>12}"
        )
        if result.error:
            print(f"    error: {result.error}")


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    settings = get_settings()
    service = build_default_textbook_embedding_ingestion_service(settings=settings)

    if args.document_id:
        document_ids = [args.document_id]
    else:
        registry = SQLiteDocumentRegistry(db_path=settings.document_registry_db_path_resolved)
        document_ids = [
            doc.id for doc in registry.list_all(approval_status=ApprovalStatus.APPROVED_FOR_POC)
        ]
        if not document_ids:
            print("No APPROVED_FOR_POC documents found.")
            return 0

    results: list[TextbookEmbeddingIngestionResult] = []
    exit_code = 0
    for document_id in document_ids:
        try:
            result = service.ingest(document_id, force=args.force, progress=print)
        except IngestionError as exc:
            print(f"Failed to ingest {document_id}: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        results.append(result)
        if result.status.value == "FAILED":
            exit_code = 1
        print()

    _print_summary(results)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
