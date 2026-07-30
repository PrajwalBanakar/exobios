import pytest

from app.embeddings.exceptions import EmbeddingGenerationError
from app.embeddings.providers.openai_provider import OpenAIEmbeddingProvider
from app.embeddings.vectorstores.qdrant_store import QdrantVectorStore
from app.retrieval.exceptions import SearchError
from app.retrieval.models.retrieval import SearchRequest
from app.retrieval.ranking.reranker import ScoreReranker
from app.retrieval.retrievers.semantic_retriever import SemanticRetriever
from app.retrieval.services.retrieval_service import RetrievalService
from tests.embeddings.conftest import FakeOpenAIClient, make_scored_point, make_search_payload


def _build_service(fake_openai_client, fake_qdrant_client, **service_kwargs) -> RetrievalService:
    provider = OpenAIEmbeddingProvider(api_key="test-key", client=fake_openai_client)
    vector_store = QdrantVectorStore(
        client=fake_qdrant_client, collection_name="exobios_chunks", vector_size=provider.dimensions
    )
    retriever = SemanticRetriever(vector_store=vector_store)
    reranker = ScoreReranker()
    defaults = {"top_k": 20, "min_score": 0.0, "max_returned_chunks": 10}
    defaults.update(service_kwargs)
    return RetrievalService(
        embedding_provider=provider, retriever=retriever, reranker=reranker, **defaults
    )


def test_end_to_end_semantic_search_returns_ranked_chunks(fake_openai_client, fake_qdrant_client):
    payload_a = make_search_payload()
    payload_b = make_search_payload()
    fake_qdrant_client.query_result = [
        make_scored_point(payload_a["chunk_id"], 0.9, payload_a),
        make_scored_point(payload_b["chunk_id"], 0.4, payload_b),
    ]
    service = _build_service(fake_openai_client, fake_qdrant_client)

    response = service.search(SearchRequest(query="fever and persistent cough"))

    assert response.query == "fever and persistent cough"
    assert response.result_count == 2
    assert [c.score for c in response.results] == [0.9, 0.4]
    assert fake_openai_client.calls == [["fever and persistent cough"]]
    assert fake_qdrant_client.query_calls[0]["limit"] == 20


def test_top_k_is_forwarded_to_vector_search(fake_openai_client, fake_qdrant_client):
    service = _build_service(fake_openai_client, fake_qdrant_client, top_k=3)

    service.search(SearchRequest(query="q"))

    assert fake_qdrant_client.query_calls[0]["limit"] == 3


def test_min_similarity_score_is_forwarded_to_vector_search(fake_openai_client, fake_qdrant_client):
    service = _build_service(fake_openai_client, fake_qdrant_client, min_score=0.65)

    service.search(SearchRequest(query="q"))

    assert fake_qdrant_client.query_calls[0]["score_threshold"] == 0.65


def test_max_returned_chunks_limits_final_results(fake_openai_client, fake_qdrant_client):
    payloads = [make_search_payload() for _ in range(5)]
    scores = [0.9, 0.8, 0.7, 0.6, 0.5]
    pairs = zip(payloads, scores, strict=True)
    fake_qdrant_client.query_result = [make_scored_point(p["chunk_id"], s, p) for p, s in pairs]
    service = _build_service(fake_openai_client, fake_qdrant_client, max_returned_chunks=2)

    response = service.search(SearchRequest(query="q"))

    assert response.result_count == 2
    assert [c.score for c in response.results] == [0.9, 0.8]


def test_duplicate_chunk_ids_are_deduplicated_keeping_highest_score(
    fake_openai_client, fake_qdrant_client
):
    payload = make_search_payload()
    fake_qdrant_client.query_result = [
        make_scored_point(payload["chunk_id"], 0.3, payload),
        make_scored_point(payload["chunk_id"], 0.95, payload),
    ]
    service = _build_service(fake_openai_client, fake_qdrant_client)

    response = service.search(SearchRequest(query="q"))

    assert response.result_count == 1
    assert response.results[0].score == 0.95


def test_search_request_can_override_service_defaults_end_to_end(
    fake_openai_client, fake_qdrant_client
):
    service = _build_service(
        fake_openai_client, fake_qdrant_client, top_k=20, min_score=0.0, max_returned_chunks=10
    )

    service.search(SearchRequest(query="q", top_k=2, min_score=0.9, max_returned_chunks=1))

    assert fake_qdrant_client.query_calls[0]["limit"] == 2
    assert fake_qdrant_client.query_calls[0]["score_threshold"] == 0.9


def test_vector_store_failure_surfaces_as_search_error(fake_openai_client, fake_qdrant_client):
    fake_qdrant_client.fail_with = RuntimeError("qdrant unreachable")
    service = _build_service(fake_openai_client, fake_qdrant_client)

    with pytest.raises(SearchError):
        service.search(SearchRequest(query="q"))


def test_embedding_failure_surfaces_as_embedding_generation_error(fake_qdrant_client):
    failing_client = FakeOpenAIClient(fail_with=RuntimeError("rate limited"))
    service = _build_service(failing_client, fake_qdrant_client)

    with pytest.raises(EmbeddingGenerationError):
        service.search(SearchRequest(query="q"))


def test_no_results_when_vector_store_has_no_matches(fake_openai_client, fake_qdrant_client):
    fake_qdrant_client.query_result = []
    service = _build_service(fake_openai_client, fake_qdrant_client)

    response = service.search(SearchRequest(query="q"))

    assert response.result_count == 0
    assert response.results == []
