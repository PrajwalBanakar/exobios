import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import prepare_textbook as cli  # noqa: E402

from app.ingestion.models.document import (  # noqa: E402
    ApprovalStatus,
    DocumentMetadata,
    DocumentStatus,
    DocumentType,
    Subject,
)
from app.ingestion.textbook.models import ProcessingSummary  # noqa: E402
from app.ingestion.textbook.service import TextbookPreparationResult  # noqa: E402


def test_cli_requires_a_target():
    parser = cli._build_arg_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_cli_rejects_both_document_id_and_all_flag():
    parser = cli._build_arg_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["--document-id", str(uuid4()), "--all-approved-poc"])


def test_cli_parses_document_id():
    parser = cli._build_arg_parser()
    document_id = uuid4()

    args = parser.parse_args(["--document-id", str(document_id)])

    assert args.document_id == document_id
    assert args.all_approved_poc is False


def test_cli_parses_show_chunks_and_chapter():
    parser = cli._build_arg_parser()

    args = parser.parse_args(
        ["--document-id", str(uuid4()), "--show-chunks", "5", "--chapter", "9"]
    )

    assert args.show_chunks == 5
    assert args.chapter == "9"


def _fake_result() -> TextbookPreparationResult:
    document_id = uuid4()
    document = DocumentMetadata(
        filename="book.pdf",
        original_path="physiology/book.pdf",
        document_type=DocumentType.PDF,
        source="manual-upload",
        checksum="abc123",
        title="Physiology",
        subject=Subject.PHYSIOLOGY,
        storage_key="physiology/book.pdf",
        approval_status=ApprovalStatus.APPROVED_FOR_POC,
        status=DocumentStatus.PENDING,
    )
    document.id = document_id
    summary = ProcessingSummary(
        document_id=document_id,
        title="Physiology",
        subject=Subject.PHYSIOLOGY,
        total_pdf_pages=1139,
        pages_with_text=1100,
        sparse_pages=30,
        possible_scanned_pages=5,
        extraction_failed_pages=0,
        chapters_detected=60,
        chunks_created=2,
        min_tokens=40,
        max_tokens=90,
        mean_tokens=65.0,
        median_tokens=65.0,
        p95_tokens=88.0,
        oversized_chunks=0,
        undersized_chunks=0,
        generated_at=datetime.now(UTC),
    )
    return TextbookPreparationResult(
        document=document,
        pages=[],
        chunks=[],
        summary=summary,
        pages_path=Path("data/extracted/x/pages.jsonl"),
        chunks_path=Path("data/processed/x/chunks.jsonl"),
        summary_path=Path("data/processed/x/summary.json"),
    )


def test_print_result_reports_key_fields(capsys):
    result = _fake_result()

    cli._print_result(result, show_chunks=0, chapter_filter=None)

    output = capsys.readouterr().out
    assert "Physiology" in output
    assert "PDF pages: 1139" in output
    assert "Detected chapters: 60" in output
    assert "Chunks generated: 2" in output
