from app.core.config import Settings
from app.retrieval.factory import build_default_retrieval_service
from app.retrieval.models.retrieval import SearchRequest
from app.retrieval.ranking.reranker import ScoreReranker
from app.retrieval.retrievers.semantic_retriever import SemanticRetriever
from tests.embeddings.conftest import make_scored_point, make_search_payload


def _settings(**overrides) -> Settings:
    defaults = {
        "AI_API_KEY": "test-ai-key",
        "OPENAI_API_KEY": "test-openai-key",
        "EMBEDDING_MODEL": "text-embedding-3-small",
        "EMBEDDING_BATCH_SIZE": 50,
        "QDRANT_URL": "http://localhost:6333",
        "QDRANT_COLLECTION": "exobios_chunks",
        "RETRIEVAL_TOP_K": 15,
        "MIN_SIMILARITY_SCORE": 0.3,
        "MAX_RETURNED_CHUNKS": 5,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def test_factory_wires_semantic_retriever_and_score_reranker(
    fake_openai_client, fake_qdrant_client
):
    settings = _settings()

    service = build_default_retrieval_service(
        settings=settings, openai_client=fake_openai_client, qdrant_client=fake_qdrant_client
    )

    assert isinstance(service._retriever, SemanticRetriever)
    assert isinstance(service._reranker, ScoreReranker)
    assert service._top_k == 15
    assert service._min_score == 0.3
    assert service._max_returned_chunks == 5


def test_factory_initializes_the_collection_when_missing(fake_openai_client, fake_qdrant_client):
    settings = _settings(QDRANT_COLLECTION="brand_new_collection")

    build_default_retrieval_service(
        settings=settings, openai_client=fake_openai_client, qdrant_client=fake_qdrant_client
    )

    assert fake_qdrant_client.created_collections
    name, _ = fake_qdrant_client.created_collections[0]
    assert name == "brand_new_collection"


def test_factory_skips_creation_when_collection_already_exists(
    fake_openai_client, fake_qdrant_client
):
    fake_qdrant_client._collections.add("exobios_chunks")
    settings = _settings(QDRANT_COLLECTION="exobios_chunks")

    build_default_retrieval_service(
        settings=settings, openai_client=fake_openai_client, qdrant_client=fake_qdrant_client
    )

    assert fake_qdrant_client.created_collections == []


def test_factory_built_service_searches_end_to_end(fake_openai_client, fake_qdrant_client):
    payload = make_search_payload()
    fake_qdrant_client.query_result = [make_scored_point(payload["chunk_id"], 0.77, payload)]
    settings = _settings()

    service = build_default_retrieval_service(
        settings=settings, openai_client=fake_openai_client, qdrant_client=fake_qdrant_client
    )
    response = service.search(SearchRequest(query="chest pain"))

    assert response.result_count == 1
    assert response.results[0].score == 0.77
    assert fake_openai_client.calls == [["chest pain"]]
