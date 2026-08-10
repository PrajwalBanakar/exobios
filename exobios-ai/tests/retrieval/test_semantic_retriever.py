import pytest

from app.embeddings.models.embedding import VectorMatch
from app.retrieval.exceptions import SearchError
from app.retrieval.retrievers.semantic_retriever import SemanticRetriever
from tests.embeddings.conftest import make_chunk, make_document_metadata, make_search_payload


class FakeVectorStore:
    """Stands in for VectorStore, isolating SemanticRetriever tests from any
    particular backend (Qdrant included)."""

    def __init__(
        self, matches=None, fail_with: Exception | None = None, health_result: bool = True
    ) -> None:
        self.matches = matches or []
        self.fail_with = fail_with
        self.health_result = health_result
        self.calls: list[tuple] = []

    def initialize(self) -> None:
        pass

    def upsert_chunks(self, document, embedded_chunks) -> None:
        pass

    def delete_document(self, document_id) -> None:
        pass

    def document_exists(self, document_id) -> bool:
        return False

    def search(self, query_vector, top_k, min_score=None, filters=None):
        if self.fail_with is not None:
            raise self.fail_with
        self.calls.append((query_vector, top_k, min_score, filters))
        return self.matches

    def health(self) -> bool:
        return self.health_result


def test_search_maps_vector_matches_to_retrieved_chunks():
    document = make_document_metadata(filename="report.pdf", tags=["a"], language="en")
    chunk = make_chunk(document.id, text="patient history", section_title="History")
    payload = make_search_payload(document=document, chunk=chunk)
    match = VectorMatch(id=payload["chunk_id"], score=0.87, payload=payload)
    store = FakeVectorStore(matches=[match])
    retriever = SemanticRetriever(vector_store=store)

    result = retriever.search([0.1, 0.2], top_k=5, min_score=0.5)

    assert len(result.chunks) == 1
    retrieved = result.chunks[0]
    assert retrieved.document_id == document.id
    assert retrieved.chunk_id == chunk.id
    assert retrieved.score == 0.87
    assert retrieved.text == "patient history"
    assert retrieved.section_title == "History"
    assert retrieved.document_type == document.document_type
    assert retrieved.filename == "report.pdf"
    assert retrieved.tags == ["a"]
    assert retrieved.language == "en"
    assert retrieved.version == document.version
    assert retrieved.source == document.source
    assert store.calls == [([0.1, 0.2], 5, 0.5, None)]


def test_search_defaults_missing_optional_payload_fields():
    document = make_document_metadata()
    chunk = make_chunk(document.id)
    payload = make_search_payload(document=document, chunk=chunk)
    for key in ("tags", "language", "section_title", "page_number"):
        payload.pop(key)
    match = VectorMatch(id=payload["chunk_id"], score=0.5, payload=payload)
    store = FakeVectorStore(matches=[match])
    retriever = SemanticRetriever(vector_store=store)

    result = retriever.search([0.1], top_k=1)

    retrieved = result.chunks[0]
    assert retrieved.tags == []
    assert retrieved.language is None
    assert retrieved.section_title is None
    assert retrieved.page_number is None


def test_search_defaults_missing_text_to_empty_string():
    document = make_document_metadata()
    chunk = make_chunk(document.id)
    payload = make_search_payload(document=document, chunk=chunk)
    payload.pop("text")
    match = VectorMatch(id=payload["chunk_id"], score=0.5, payload=payload)
    store = FakeVectorStore(matches=[match])
    retriever = SemanticRetriever(vector_store=store)

    result = retriever.search([0.1], top_k=1)

    assert result.chunks[0].text == ""


def test_search_returns_empty_result_when_no_matches():
    store = FakeVectorStore(matches=[])
    retriever = SemanticRetriever(vector_store=store)

    result = retriever.search([0.1], top_k=5)

    assert result.chunks == []


def test_search_wraps_vector_store_errors_as_search_error():
    store = FakeVectorStore(fail_with=RuntimeError("qdrant down"))
    retriever = SemanticRetriever(vector_store=store)

    with pytest.raises(SearchError):
        retriever.search([0.1], top_k=5)


def test_search_maps_textbook_payload_fields_when_present():
    document = make_document_metadata(filename="physiology.pdf")
    chunk = make_chunk(document.id, text="the cardiac cycle...")
    payload = make_search_payload(
        document=document,
        chunk=chunk,
        subject="PHYSIOLOGY",
        title="Guyton and Hall Textbook of Medical Physiology",
        edition="14th",
        chapter_number="9",
        chapter_title="Heart Muscle",
        subsection_title="Diastole",
        pdf_page_start=117,
        pdf_page_end=119,
        printed_page_start=106,
        printed_page_end=108,
        page_classification="MAIN_CONTENT",
    )
    match = VectorMatch(id=payload["chunk_id"], score=0.9, payload=payload)
    store = FakeVectorStore(matches=[match])
    retriever = SemanticRetriever(vector_store=store)

    retrieved = retriever.search([0.1], top_k=1).chunks[0]

    assert retrieved.subject.value == "PHYSIOLOGY"
    assert retrieved.title == "Guyton and Hall Textbook of Medical Physiology"
    assert retrieved.chapter_number == "9"
    assert retrieved.chapter_title == "Heart Muscle"
    assert retrieved.subsection_title == "Diastole"
    assert retrieved.pdf_page_start == 117
    assert retrieved.pdf_page_end == 119
    assert retrieved.printed_page_start == 106
    assert retrieved.printed_page_end == 108
    assert retrieved.page_classification == "MAIN_CONTENT"


def test_search_leaves_textbook_fields_none_for_clinical_payload():
    document = make_document_metadata()
    chunk = make_chunk(document.id)
    payload = make_search_payload(document=document, chunk=chunk)
    match = VectorMatch(id=payload["chunk_id"], score=0.5, payload=payload)
    store = FakeVectorStore(matches=[match])
    retriever = SemanticRetriever(vector_store=store)

    retrieved = retriever.search([0.1], top_k=1).chunks[0]

    assert retrieved.subject is None
    assert retrieved.chapter_number is None
    assert retrieved.pdf_page_start is None


def test_health_delegates_to_vector_store():
    store = FakeVectorStore(health_result=False)
    retriever = SemanticRetriever(vector_store=store)

    assert retriever.health() is False
