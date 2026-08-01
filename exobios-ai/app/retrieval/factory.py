from google import genai
from openai import OpenAI
from qdrant_client import QdrantClient

from app.core.config import Settings, get_settings
from app.embeddings.providers.base import EmbeddingProvider
from app.embeddings.providers.gemini_provider import GeminiEmbeddingProvider
from app.embeddings.providers.openai_provider import OpenAIEmbeddingProvider
from app.embeddings.vectorstores.qdrant_store import QdrantVectorStore
from app.retrieval.ranking.reranker import ScoreReranker
from app.retrieval.retrievers.semantic_retriever import SemanticRetriever
from app.retrieval.services.retrieval_service import RetrievalService


def build_default_retrieval_service(
    settings: Settings | None = None,
    openai_client: OpenAI | None = None,
    gemini_client: genai.Client | None = None,
    qdrant_client: QdrantClient | None = None,
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
    """
    settings = settings or get_settings()

    provider: EmbeddingProvider
    if settings.gemini_api_key:
        provider = GeminiEmbeddingProvider(
            api_key=settings.gemini_api_key,
            model=settings.embedding_model,
            batch_size=settings.embedding_batch_size,
            client=gemini_client,
        )
    else:
        provider = OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.embedding_model,
            batch_size=settings.embedding_batch_size,
            client=openai_client,
        )

    client = qdrant_client or QdrantClient(
        url=settings.qdrant_url, api_key=settings.qdrant_api_key
    )
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection,
        vector_size=provider.dimensions,
    )
    vector_store.initialize()

    retriever = SemanticRetriever(vector_store=vector_store)
    reranker = ScoreReranker()

    return RetrievalService(
        embedding_provider=provider,
        retriever=retriever,
        reranker=reranker,
        top_k=settings.retrieval_top_k,
        min_score=settings.min_similarity_score,
        max_returned_chunks=settings.max_returned_chunks,
    )
