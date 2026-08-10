import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.ingestion.models.document import Subject
from app.ingestion.textbook.artifacts import TextbookArtifactWriter
from app.ingestion.textbook.models import (
    ExtractionStatus,
    PageClassification,
    PageExtraction,
    ProcessingSummary,
    StructureState,
    TextbookChunk,
    TextbookChunkMetadata,
)


def _page(document_id) -> PageExtraction:
    return PageExtraction(
        document_id=document_id,
        pdf_page_number=1,
        printed_page_number=106,
        raw_text="raw",
        cleaned_text="cleaned",
        extraction_status=ExtractionStatus.TEXT_OK,
        classification=PageClassification.MAIN_CONTENT,
        headings=[],
        structure_after=StructureState(),
    )


def _chunk(document_id) -> TextbookChunk:
    return TextbookChunk(
        text="Chapter 9\n\nThe cardiac cycle...",
        metadata=TextbookChunkMetadata(
            document_id=document_id,
            subject=Subject.PHYSIOLOGY,
            title="Physiology",
            edition="14th",
            unit_or_section="The Heart",
            chapter_number="9",
            chapter_title="Heart Muscle",
            section_title="The Cardiac Cycle",
            subsection_title=None,
            pdf_page_start=117,
            pdf_page_end=119,
            printed_page_start=106,
            printed_page_end=108,
            chunk_index=0,
            token_count=42,
            page_classification=PageClassification.MAIN_CONTENT,
        ),
    )


def _summary(document_id) -> ProcessingSummary:
    return ProcessingSummary(
        document_id=document_id,
        title="Physiology",
        subject=Subject.PHYSIOLOGY,
        total_pdf_pages=1139,
        pages_with_text=1100,
        sparse_pages=30,
        possible_scanned_pages=5,
        extraction_failed_pages=0,
        chapters_detected=60,
        chunks_created=2000,
        min_tokens=10,
        max_tokens=800,
        mean_tokens=500.0,
        median_tokens=490.0,
        p95_tokens=780.0,
        oversized_chunks=3,
        undersized_chunks=12,
        generated_at=datetime.now(UTC),
    )


def test_write_pages_creates_jsonl(tmp_path: Path):
    writer = TextbookArtifactWriter(
        extracted_root=tmp_path / "extracted", processed_root=tmp_path / "processed"
    )
    document_id = uuid4()

    path = writer.write_pages(document_id, [_page(document_id), _page(document_id)])

    assert path.is_file()
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        parsed = json.loads(line)
        assert parsed["pdf_page_number"] == 1


def test_write_chunks_creates_jsonl(tmp_path: Path):
    writer = TextbookArtifactWriter(
        extracted_root=tmp_path / "extracted", processed_root=tmp_path / "processed"
    )
    document_id = uuid4()

    path = writer.write_chunks(document_id, [_chunk(document_id)])

    assert path.is_file()
    parsed = json.loads(path.read_text(encoding="utf-8").strip())
    assert parsed["metadata"]["chapter_number"] == "9"


def test_write_summary_creates_json(tmp_path: Path):
    writer = TextbookArtifactWriter(
        extracted_root=tmp_path / "extracted", processed_root=tmp_path / "processed"
    )
    document_id = uuid4()

    path = writer.write_summary(document_id, _summary(document_id))

    assert path.is_file()
    parsed = json.loads(path.read_text(encoding="utf-8"))
    assert parsed["chunks_created"] == 2000
    assert parsed["total_pdf_pages"] == 1139


def test_artifact_paths_are_confined_to_configured_roots(tmp_path: Path):
    extracted_root = tmp_path / "extracted"
    processed_root = tmp_path / "processed"
    writer = TextbookArtifactWriter(extracted_root=extracted_root, processed_root=processed_root)
    document_id = uuid4()

    pages_path = writer.write_pages(document_id, [_page(document_id)])
    chunks_path = writer.write_chunks(document_id, [_chunk(document_id)])
    summary_path = writer.write_summary(document_id, _summary(document_id))

    assert pages_path.is_relative_to(extracted_root)
    assert chunks_path.is_relative_to(processed_root)
    assert summary_path.is_relative_to(processed_root)


def test_written_artifacts_round_trip_through_the_pydantic_models(tmp_path: Path):
    writer = TextbookArtifactWriter(
        extracted_root=tmp_path / "extracted", processed_root=tmp_path / "processed"
    )
    document_id = uuid4()
    original_page = _page(document_id)
    original_chunk = _chunk(document_id)

    pages_path = writer.write_pages(document_id, [original_page])
    chunks_path = writer.write_chunks(document_id, [original_chunk])

    reloaded_page = PageExtraction.model_validate_json(
        pages_path.read_text(encoding="utf-8").strip()
    )
    reloaded_chunk = TextbookChunk.model_validate_json(
        chunks_path.read_text(encoding="utf-8").strip()
    )

    assert reloaded_page == original_page
    assert reloaded_chunk == original_chunk
