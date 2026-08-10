from google import genai
from openai import OpenAI
from qdrant_client import QdrantClient

from app.core.config import Settings, get_settings
from app.embeddings.factory import build_default_embedding_provider_and_store
from app.retrieval.ranking.reranker import ScoreReranker
from app.retrieval.retrievers.semantic_retriever import SemanticRetriever
from app.retrieval.services.retrieval_service import RetrievalService


def build_default_retrieval_service(
    settings: Settings | None = None,
    openai_client: OpenAI | None = None,
    gemini_client: genai.Client | None = None,
    qdrant_client: QdrantClient | None = None,
    collection_name: str | None = None,
    min_score: float | None = None,
) -> RetrievalService:
    """Composition root wiring an EmbeddingProvider + SemanticRetriever
    (backed by QdrantVectorStore) + ScoreReranker into a RetrievalService.
    Builds GeminiEmbeddingProvider when GEMINI_API_KEY is configured (a
    free-tier alternative for local dev/demo use) and OpenAIEmbeddingProvider
    otherwise — must match app.embeddings.factory's choice, since ingestion
    and retrieval have to embed with the same provider/model for vector
    search to be meaningful. `openai_client`/`gemini_client`/`qdrant_client`
    are injectable so tests (and alternative deployments) can supply fakes
    instead of the real network clients built from `settings`.

    `collection_name`/`min_score` default to the IMNCI clinical-guideline
    settings (`qdrant_collection`/`min_similarity_score`) — AI-7C's textbook
    Q&A passes `qdrant_textbook_collection`/`textbook_min_retrieval_score`
    explicitly.
    """
    settings = settings or get_settings()

    provider, vector_store = build_default_embedding_provider_and_store(
        settings=settings,
        openai_client=openai_client,
        gemini_client=gemini_client,
        qdrant_client=qdrant_client,
        collection_name=collection_name,
    )

    retriever = SemanticRetriever(vector_store=vector_store)
    reranker = ScoreReranker()

    return RetrievalService(
        embedding_provider=provider,
        retriever=retriever,
        reranker=reranker,
        top_k=settings.retrieval_top_k,
        min_score=min_score if min_score is not None else settings.min_similarity_score,
        max_returned_chunks=settings.max_returned_chunks,
    )
