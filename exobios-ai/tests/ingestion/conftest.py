import io
from collections.abc import Callable

import fitz
import pytest
from docx import Document as DocxDocument

from app.ingestion.models.chunk import Chunk
from app.ingestion.models.document import DocumentMetadata


class FakeEmbeddingService:
    """Records embed_document calls without touching OpenAI/Qdrant.

    Ingestion tests care that IngestionService *calls* the embedding step at
    the right point in the pipeline, not about embedding correctness itself
    (that's covered by tests/embeddings) — so a lightweight recorder is
    enough here and keeps these tests free of network/mocking concerns.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[DocumentMetadata, list[Chunk]]] = []

    def embed_document(self, document: DocumentMetadata, chunks: list[Chunk]) -> int:
        self.calls.append((document, chunks))
        return len(chunks)


@pytest.fixture
def fake_embedding_service() -> FakeEmbeddingService:
    return FakeEmbeddingService()


@pytest.fixture
def pdf_bytes_factory() -> Callable[[list[str]], bytes]:
    def _make(pages_text: list[str]) -> bytes:
        document = fitz.open()
        for text in pages_text:
            page = document.new_page()
            page.insert_text((72, 72), text)
        data = document.tobytes()
        document.close()
        return data

    return _make


@pytest.fixture
def docx_bytes_factory() -> Callable[[list[str]], bytes]:
    def _make(paragraphs: list[str]) -> bytes:
        document = DocxDocument()
        for paragraph in paragraphs:
            document.add_paragraph(paragraph)
        buffer = io.BytesIO()
        document.save(buffer)
        return buffer.getvalue()

    return _make
