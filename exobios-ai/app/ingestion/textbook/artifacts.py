from pathlib import Path
from uuid import UUID

from app.ingestion.textbook.exceptions import TextbookProcessingError
from app.ingestion.textbook.models import PageExtraction, ProcessingSummary, TextbookChunk


class ChunksArtifactMissingError(TextbookProcessingError):
    def __init__(self, document_id: UUID, path: Path) -> None:
        self.document_id = document_id
        super().__init__(
            status_code=404,
            code="CHUNKS_ARTIFACT_MISSING",
            message=f"No chunks.jsonl found for document {document_id} at {path} — run "
            "scripts/prepare_textbook.py for this document first",
        )


class TextbookArtifactWriter:
    """Writes dev-inspection artifacts under data/extracted/<document_id>/
    and data/processed/<document_id>/ — both roots come from Settings, so
    every path this class produces is confined to the configured data
    directories (the same ones AI-7A git-ignores). Original PDFs are never
    read or written by this class."""

    def __init__(self, extracted_root: Path, processed_root: Path) -> None:
        self._extracted_root = Path(extracted_root)
        self._processed_root = Path(processed_root)

    def write_pages(self, document_id: UUID, pages: list[PageExtraction]) -> Path:
        out_dir = self._extracted_root / str(document_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "pages.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for page in pages:
                handle.write(page.model_dump_json())
                handle.write("\n")
        return path

    def write_chunks(self, document_id: UUID, chunks: list[TextbookChunk]) -> Path:
        out_dir = self._processed_root / str(document_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "chunks.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for chunk in chunks:
                handle.write(chunk.model_dump_json())
                handle.write("\n")
        return path

    def write_summary(self, document_id: UUID, summary: ProcessingSummary) -> Path:
        out_dir = self._processed_root / str(document_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "summary.json"
        path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
        return path

    def chunks_path(self, document_id: UUID) -> Path:
        return self._processed_root / str(document_id) / "chunks.jsonl"

    def read_chunks(self, document_id: UUID) -> list[TextbookChunk]:
        """Reads back a previously-written chunks.jsonl — the source AI-7C
        embeds from, per its explicit instruction not to re-extract/re-chunk
        PDFs that AI-7B already validated."""
        path = self.chunks_path(document_id)
        if not path.is_file():
            raise ChunksArtifactMissingError(document_id=document_id, path=path)

        chunks: list[TextbookChunk] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped:
                    chunks.append(TextbookChunk.model_validate_json(stripped))
        return chunks
