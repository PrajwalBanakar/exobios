from uuid import uuid4

import pytest

from app.ingestion.models.document import DocumentType, Subject
from app.retrieval.models.retrieval import RetrievedChunk


def make_textbook_chunk(**overrides) -> RetrievedChunk:
    defaults = {
        "document_id": uuid4(),
        "chunk_id": uuid4(),
        "score": 0.8,
        "text": "The cardiac cycle refers to the sequence of events in one heartbeat.",
        "page_number": 117,
        "section_title": "The Cardiac Cycle",
        "document_type": DocumentType.PDF,
        "filename": "physiology.pdf",
        "language": "en",
        "tags": [],
        "version": "1.0",
        "source": "manual-upload",
        "subject": Subject.PHYSIOLOGY,
        "title": "Guyton and Hall Textbook of Medical Physiology",
        "edition": "14th",
        "chapter_number": "9",
        "chapter_title": "Heart Muscle",
        "pdf_page_start": 117,
        "pdf_page_end": 119,
        "printed_page_start": 106,
        "printed_page_end": 108,
    }
    defaults.update(overrides)
    return RetrievedChunk(**defaults)


@pytest.fixture
def textbook_chunk_factory():
    return make_textbook_chunk
