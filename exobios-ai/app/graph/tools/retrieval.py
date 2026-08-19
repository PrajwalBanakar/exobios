from schemas.stages.common import SupportingCitation
from services.embedding_service import embedding_service
from services.qdrant_service import qdrant_service
from services.reranker_service import reranker_service


def retrieve_and_rerank(query_text: str, filters: dict, top_k: int = 8) -> list[SupportingCitation]:
    """embed query -> Qdrant hybrid (dense+sparse, RRF fused) search -> rerank.
    No domain knowledge here — same function is called by diagnosis,
    investigation, and treatment nodes with different query/filters."""
    dense_vector = embedding_service.embed(query_text)
    candidates = qdrant_service.hybrid_search(query_text, dense_vector, filters, top_k=top_k * 2)
    reranked = reranker_service.rerank(query_text, candidates, top_k=top_k)

    citations = []
    for c in reranked:
        chunk_meta = c["payload"].get("chunk_payload", {}).get("chunk_metadata", {})
        doc_meta = c["payload"].get("document_payload", {})
        citations.append(SupportingCitation(
            chunk_id=c["chunk_id"],
            document_id=doc_meta.get("document_id", ""),
            excerpt=chunk_meta.get("content", ""),
            heading=chunk_meta.get("heading", ""),
            page=chunk_meta.get("page_start", 0),
        ))
    return citations