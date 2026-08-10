"""Extract + structure-aware chunk a registered textbook — a dry-run
preparation step (AI-7B). Reads the PDF through DocumentStorage by its
registered storage_key, never embeds anything, never touches Qdrant, and
never mutates the registry. Writes inspectable artifacts to
data/extracted/<document_id>/pages.jsonl and
data/processed/<document_id>/{chunks.jsonl,summary.json}.

    python scripts/prepare_textbook.py --document-id <uuid>
    python scripts/prepare_textbook.py --document-id <uuid> --show-chunks 5
    python scripts/prepare_textbook.py --document-id <uuid> --show-chunks 5 --chapter 9
    python scripts/prepare_textbook.py --all-approved-poc
"""

import argparse
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parent.parent))

# Extracted PDF text routinely contains characters (en-spaces, ligatures,
# Greek letters, special dashes) the default Windows console codepage
# (cp1252) can't encode — reconfigure stdout/stderr to UTF-8 so printing a
# chunk preview never crashes the run. errors="replace" so an even rarer
# unencodable character degrades to "?" instead of aborting.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.core.config import get_settings  # noqa: E402
from app.ingestion.exceptions import IngestionError  # noqa: E402
from app.ingestion.models.document import ApprovalStatus  # noqa: E402
from app.ingestion.registry.sqlite_registry import SQLiteDocumentRegistry  # noqa: E402
from app.ingestion.textbook.factory import build_default_textbook_preparation_service  # noqa: E402
from app.ingestion.textbook.service import TextbookPreparationResult  # noqa: E402

_PREVIEW_CHARS = 300


def _print_result(
    result: TextbookPreparationResult, show_chunks: int, chapter_filter: str | None
) -> None:
    document = result.document
    summary = result.summary

    print(f"Document: {document.title or document.filename} ({document.id})")
    print(f"Subject: {document.subject.value if document.subject else '-'}")
    print(f"PDF pages: {summary.total_pdf_pages}")
    print(f"Text pages: {summary.pages_with_text}")
    print(f"Sparse pages: {summary.sparse_pages}")
    print(f"Possible scanned pages: {summary.possible_scanned_pages}")
    print(f"Extraction failed pages: {summary.extraction_failed_pages}")
    print(f"Detected chapters: {summary.chapters_detected}")
    print(f"Chunks generated: {summary.chunks_created}")
    if summary.chunks_created:
        print(f"Average tokens/chunk: {summary.mean_tokens}")
        print(f"Median tokens/chunk: {summary.median_tokens}")
        print(f"95th percentile tokens/chunk: {summary.p95_tokens}")
        print(f"Largest chunk: {summary.max_tokens} tokens")
        print(f"Smallest chunk: {summary.min_tokens} tokens")
        print(f"Oversized chunks (> max budget): {summary.oversized_chunks}")
        print(f"Undersized chunks (< min useful): {summary.undersized_chunks}")
    print("Artifacts:")
    print(f"  {result.pages_path}")
    print(f"  {result.chunks_path}")
    print(f"  {result.summary_path}")

    if show_chunks <= 0:
        return

    chunks = result.chunks
    if chapter_filter:
        chunks = [c for c in chunks if c.metadata.chapter_number == chapter_filter]

    print(f"\nShowing {min(show_chunks, len(chunks))} of {len(chunks)} matching chunk(s):")
    for chunk in chunks[:show_chunks]:
        meta = chunk.metadata
        print("-" * 70)
        print(
            f"chunk_index={meta.chunk_index} tokens={meta.token_count} "
            f"pdf_pages={meta.pdf_page_start}-{meta.pdf_page_end} "
            f"printed_pages={meta.printed_page_start}-{meta.printed_page_end}"
        )
        print(
            f"unit_or_section={meta.unit_or_section!r} chapter={meta.chapter_number!r} "
            f"chapter_title={meta.chapter_title!r}"
        )
        print(f"section={meta.section_title!r} subsection={meta.subsection_title!r}")
        preview = chunk.text[:_PREVIEW_CHARS].replace("\n", " ")
        suffix = "..." if len(chunk.text) > _PREVIEW_CHARS else ""
        print(preview + suffix)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract + chunk a registered textbook (dry-run, no embeddings/Qdrant)."
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--document-id", type=UUID, help="Registered document_id to process")
    target.add_argument(
        "--all-approved-poc",
        action="store_true",
        help="Process every document with approval_status=APPROVED_FOR_POC",
    )
    parser.add_argument(
        "--show-chunks", type=int, default=0, help="Print the first N generated chunks"
    )
    parser.add_argument(
        "--chapter", type=str, default=None, help="Only show chunks from this chapter_number"
    )
    return parser


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    settings = get_settings()
    service = build_default_textbook_preparation_service(settings=settings)

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

    exit_code = 0
    for index, document_id in enumerate(document_ids):
        if index > 0:
            print("\n" + "=" * 70 + "\n")
        try:
            result = service.prepare(document_id)
        except IngestionError as exc:
            print(f"Failed to prepare {document_id}: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        _print_result(result, args.show_chunks, args.chapter)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
