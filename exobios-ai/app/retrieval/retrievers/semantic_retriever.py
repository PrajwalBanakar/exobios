from app.embeddings.models.embedding import VectorMatch
from app.embeddings.vectorstores.base import VectorStore
from app.retrieval.exceptions import SearchError
from app.retrieval.models.retrieval import RetrievedChunk, SearchResult
from app.retrieval.retrievers.base import Retriever


class SemanticRetriever(Retriever):
    """Retrieves candidate chunks via cosine-similarity vector search.
    Depends only on the VectorStore interface — knows nothing about Qdrant,
    or any other backend, specifically.

    Any vector-store failure (including an already-specific VectorStoreError)
    is normalized to SearchError, since from the retrieval layer's point of
    view "the candidate search failed" is the meaningful fact — the backend
    that failed is an implementation detail of the injected VectorStore.
    """

    def __init__(self, vector_store: VectorStore) -> None:
        self._vector_store = vector_store

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        min_score: float | None = None,
        filters: dict[str, object] | None = None,
    ) -> SearchResult:
        try:
            matches = self._vector_store.search(
                query_vector, top_k=top_k, min_score=min_score, filters=filters
            )
        except Exception as exc:
            raise SearchError(reason=str(exc)) from exc

        return SearchResult(chunks=[self._to_retrieved_chunk(match) for match in matches])

    def health(self) -> bool:
        return self._vector_store.health()

    def _to_retrieved_chunk(self, match: VectorMatch) -> RetrievedChunk:
        # Payload comes from an external system (Qdrant), so every field is
        # read defensively — a system boundary is exactly where that's
        # warranted, rather than trusting it matches what upsert_chunks wrote.
        # The textbook-specific keys (subject through page_classification)
        # are simply absent on clinical-guideline payloads, so .get()
        # correctly leaves them None for that path.
        payload = match.payload
        return RetrievedChunk(
            document_id=payload["document_id"],
            chunk_id=payload["chunk_id"],
            score=match.score,
            text=payload.get("text", ""),
            page_number=payload.get("page_number"),
            section_title=payload.get("section_title"),
            document_type=payload["document_type"],
            filename=payload["filename"],
            language=payload.get("language"),
            tags=payload.get("tags") or [],
            version=payload["version"],
            source=payload["source"],
            subject=payload.get("subject"),
            title=payload.get("title"),
            edition=payload.get("edition"),
            unit_or_section=payload.get("unit_or_section"),
            chapter_number=payload.get("chapter_number"),
            chapter_title=payload.get("chapter_title"),
            subsection_title=payload.get("subsection_title"),
            pdf_page_start=payload.get("pdf_page_start"),
            pdf_page_end=payload.get("pdf_page_end"),
            printed_page_start=payload.get("printed_page_start"),
            printed_page_end=payload.get("printed_page_end"),
            page_classification=payload.get("page_classification"),
        )
