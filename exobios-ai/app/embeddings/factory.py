from openai import OpenAI
from qdrant_client import QdrantClient

from app.core.config import Settings, get_settings
from app.embeddings.providers.openai_provider import OpenAIEmbeddingProvider
from app.embeddings.services.embedding_service import EmbeddingService
from app.embeddings.vectorstores.qdrant_store import QdrantVectorStore


def build_default_embedding_service(
    settings: Settings | None = None,
    openai_client: OpenAI | None = None,
    qdrant_client: QdrantClient | None = None,
) -> EmbeddingService:
    """Composition root wiring OpenAIEmbeddingProvider + QdrantVectorStore
    into an EmbeddingService. `openai_client`/`qdrant_client` are injectable
    so tests (and alternative deployments) can supply fakes instead of the
    real network clients built from `settings`.
    """
    settings = settings or get_settings()

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

    return EmbeddingService(provider=provider, vector_store=vector_store)
