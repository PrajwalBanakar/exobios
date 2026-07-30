import logging
import time

from app.embeddings.exceptions import EmbeddingGenerationError
from app.embeddings.providers.base import EmbeddingProvider
from app.retrieval.exceptions import RetrievalError, SearchError
from app.retrieval.models.retrieval import (
    RetrievedChunk,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from app.retrieval.ranking.reranker import Reranker
from app.retrieval.retrievers.base import Retriever

logger = logging.getLogger("app.retrieval")


class RetrievalService:
    """Orchestrates: embed query -> retrieve candidates -> rerank -> respond.

    Depends only on EmbeddingProvider, Retriever, and Reranker interfaces —
    no OpenAI or Qdrant specifics leak in here. Top-K, minimum similarity
    score, and the maximum number of returned chunks all have service-level
    defaults (from configuration) that a SearchRequest can override per call.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        retriever: Retriever,
        reranker: Reranker,
        top_k: int = 20,
        min_score: float = 0.0,
        max_returned_chunks: int = 10,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._retriever = retriever
        self._reranker = reranker
        self._top_k = top_k
        self._min_score = min_score
        self._max_returned_chunks = max_returned_chunks

    def search(self, request: SearchRequest) -> SearchResponse:
        start = time.perf_counter()
        query = request.query
        query_length = len(query)
        top_k = request.top_k if request.top_k is not None else self._top_k
        min_score = request.min_score if request.min_score is not None else self._min_score
        max_returned_chunks = (
            request.max_returned_chunks
            if request.max_returned_chunks is not None
            else self._max_returned_chunks
        )

        logger.info("retrieval_started query_length=%s top_k=%s", query_length, top_k)

        query_vector = self._embed_query(query, query_length)
        search_result = self._retrieve(query_vector, top_k, min_score, query_length)
        ranked = self._rerank(search_result.chunks, max_returned_chunks, query_length)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "retrieval_completed query_length=%s retrieved_chunks=%s elapsed_time=%s",
            query_length,
            len(ranked),
            elapsed_ms,
        )

        return SearchResponse(
            query=query, results=ranked, result_count=len(ranked), elapsed_ms=elapsed_ms
        )

    def _embed_query(self, query: str, query_length: int) -> list[float]:
        try:
            query_vector = self._embedding_provider.embed_text(query)
        except EmbeddingGenerationError:
            logger.error("retrieval_failed query_length=%s stage=embedding", query_length)
            raise
        except Exception as exc:
            logger.error("retrieval_failed query_length=%s stage=embedding", query_length)
            raise RetrievalError(reason=str(exc)) from exc

        logger.info(
            "query_embedded query_length=%s dimensions=%s", query_length, len(query_vector)
        )
        return query_vector

    def _retrieve(
        self, query_vector: list[float], top_k: int, min_score: float, query_length: int
    ) -> SearchResult:
        try:
            search_result = self._retriever.search(query_vector, top_k=top_k, min_score=min_score)
        except SearchError:
            logger.error("retrieval_failed query_length=%s stage=vector_search", query_length)
            raise
        except Exception as exc:
            logger.error("retrieval_failed query_length=%s stage=vector_search", query_length)
            raise RetrievalError(reason=str(exc)) from exc

        logger.info(
            "vector_search_completed query_length=%s retrieved_chunks=%s",
            query_length,
            len(search_result.chunks),
        )
        return search_result

    def _rerank(
        self, chunks: list[RetrievedChunk], max_returned_chunks: int, query_length: int
    ) -> list[RetrievedChunk]:
        try:
            ranked = self._reranker.rerank(chunks, max_results=max_returned_chunks)
        except Exception as exc:
            logger.error("retrieval_failed query_length=%s stage=reranking", query_length)
            raise RetrievalError(reason=str(exc)) from exc

        logger.info(
            "reranking_completed query_length=%s retrieved_chunks=%s", query_length, len(ranked)
        )
        return ranked
