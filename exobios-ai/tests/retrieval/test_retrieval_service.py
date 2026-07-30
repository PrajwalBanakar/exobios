import pytest

from app.embeddings.exceptions import EmbeddingGenerationError
from app.retrieval.exceptions import RetrievalError, SearchError
from app.retrieval.models.retrieval import SearchRequest, SearchResult
from app.retrieval.services.retrieval_service import RetrievalService
from tests.retrieval.conftest import (
    FakeEmbeddingProvider,
    FakeReranker,
    FakeRetriever,
    make_retrieved_chunk,
)


def test_search_happy_path_embeds_retrieves_and_reranks():
    chunk = make_retrieved_chunk(score=0.8)
    retriever = FakeRetriever(result=SearchResult(chunks=[chunk]))
    reranker = FakeReranker()
    provider = FakeEmbeddingProvider()
    service = RetrievalService(embedding_provider=provider, retriever=retriever, reranker=reranker)

    response = service.search(SearchRequest(query="fever and cough"))

    assert response.query == "fever and cough"
    assert response.results == [chunk]
    assert response.result_count == 1
    assert response.elapsed_ms >= 0
    assert provider.embedded_texts == ["fever and cough"]
    assert retriever.calls[0][1] == 20  # default top_k
    assert reranker.calls[0][1] == 10  # default max_returned_chunks


def test_search_request_overrides_service_defaults():
    retriever = FakeRetriever(result=SearchResult(chunks=[]))
    reranker = FakeReranker()
    provider = FakeEmbeddingProvider()
    service = RetrievalService(
        embedding_provider=provider,
        retriever=retriever,
        reranker=reranker,
        top_k=20,
        min_score=0.0,
        max_returned_chunks=10,
    )

    service.search(SearchRequest(query="q", top_k=3, min_score=0.75, max_returned_chunks=2))

    _, top_k, min_score = retriever.calls[0]
    assert top_k == 3
    assert min_score == 0.75
    assert reranker.calls[0][1] == 2


def test_search_uses_configured_defaults_when_request_omits_overrides():
    retriever = FakeRetriever(result=SearchResult(chunks=[]))
    reranker = FakeReranker()
    provider = FakeEmbeddingProvider()
    service = RetrievalService(
        embedding_provider=provider,
        retriever=retriever,
        reranker=reranker,
        top_k=7,
        min_score=0.42,
        max_returned_chunks=3,
    )

    service.search(SearchRequest(query="q"))

    _, top_k, min_score = retriever.calls[0]
    assert top_k == 7
    assert min_score == 0.42
    assert reranker.calls[0][1] == 3


def test_search_propagates_embedding_generation_error():
    provider = FakeEmbeddingProvider(fail_with=EmbeddingGenerationError(reason="rate limited"))
    retriever = FakeRetriever()
    reranker = FakeReranker()
    service = RetrievalService(embedding_provider=provider, retriever=retriever, reranker=reranker)

    with pytest.raises(EmbeddingGenerationError):
        service.search(SearchRequest(query="q"))

    assert retriever.calls == []


def test_search_wraps_unexpected_embedding_exception_as_retrieval_error():
    provider = FakeEmbeddingProvider(fail_with=RuntimeError("boom"))
    retriever = FakeRetriever()
    reranker = FakeReranker()
    service = RetrievalService(embedding_provider=provider, retriever=retriever, reranker=reranker)

    with pytest.raises(RetrievalError):
        service.search(SearchRequest(query="q"))


def test_search_propagates_search_error_from_retriever():
    provider = FakeEmbeddingProvider()
    retriever = FakeRetriever(fail_with=SearchError(reason="qdrant down"))
    reranker = FakeReranker()
    service = RetrievalService(embedding_provider=provider, retriever=retriever, reranker=reranker)

    with pytest.raises(SearchError):
        service.search(SearchRequest(query="q"))

    assert reranker.calls == []


def test_search_wraps_unexpected_retriever_exception_as_retrieval_error():
    provider = FakeEmbeddingProvider()
    retriever = FakeRetriever(fail_with=RuntimeError("boom"))
    reranker = FakeReranker()
    service = RetrievalService(embedding_provider=provider, retriever=retriever, reranker=reranker)

    with pytest.raises(RetrievalError):
        service.search(SearchRequest(query="q"))


def test_search_wraps_reranker_exception_as_retrieval_error():
    provider = FakeEmbeddingProvider()
    retriever = FakeRetriever(result=SearchResult(chunks=[make_retrieved_chunk()]))
    reranker = FakeReranker(fail_with=RuntimeError("boom"))
    service = RetrievalService(embedding_provider=provider, retriever=retriever, reranker=reranker)

    with pytest.raises(RetrievalError):
        service.search(SearchRequest(query="q"))


def test_search_logs_each_pipeline_stage(caplog):
    chunk = make_retrieved_chunk()
    retriever = FakeRetriever(result=SearchResult(chunks=[chunk]))
    reranker = FakeReranker()
    provider = FakeEmbeddingProvider()
    service = RetrievalService(embedding_provider=provider, retriever=retriever, reranker=reranker)

    with caplog.at_level("INFO", logger="app.retrieval"):
        service.search(SearchRequest(query="q"))

    messages = " ".join(record.message for record in caplog.records)
    for expected in (
        "retrieval_started",
        "query_embedded",
        "vector_search_completed",
        "reranking_completed",
        "retrieval_completed",
    ):
        assert expected in messages


def test_search_logs_retrieval_failed_on_embedding_error(caplog):
    provider = FakeEmbeddingProvider(fail_with=RuntimeError("boom"))
    retriever = FakeRetriever()
    reranker = FakeReranker()
    service = RetrievalService(embedding_provider=provider, retriever=retriever, reranker=reranker)

    with caplog.at_level("ERROR", logger="app.retrieval"), pytest.raises(RetrievalError):
        service.search(SearchRequest(query="q"))

    assert any("retrieval_failed" in record.message for record in caplog.records)


def test_search_logs_retrieval_failed_on_search_error(caplog):
    provider = FakeEmbeddingProvider()
    retriever = FakeRetriever(fail_with=SearchError(reason="down"))
    reranker = FakeReranker()
    service = RetrievalService(embedding_provider=provider, retriever=retriever, reranker=reranker)

    with caplog.at_level("ERROR", logger="app.retrieval"), pytest.raises(SearchError):
        service.search(SearchRequest(query="q"))

    assert any("retrieval_failed" in record.message for record in caplog.records)
