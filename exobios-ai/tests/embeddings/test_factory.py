from app.core.config import Settings
from app.embeddings.factory import build_default_embedding_service
from app.embeddings.providers.openai_provider import OpenAIEmbeddingProvider
from app.embeddings.vectorstores.qdrant_store import QdrantVectorStore


def _settings(**overrides) -> Settings:
    defaults = {
        "AI_API_KEY": "test-ai-key",
        "OPENAI_API_KEY": "test-openai-key",
        "EMBEDDING_MODEL": "text-embedding-3-small",
        "EMBEDDING_BATCH_SIZE": 50,
        "QDRANT_URL": "http://localhost:6333",
        "QDRANT_COLLECTION": "exobios_chunks",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def test_factory_wires_openai_provider_and_qdrant_store(fake_openai_client, fake_qdrant_client):
    settings = _settings()

    service = build_default_embedding_service(
        settings=settings, openai_client=fake_openai_client, qdrant_client=fake_qdrant_client
    )

    provider = service._provider
    store = service._vector_store
    assert isinstance(provider, OpenAIEmbeddingProvider)
    assert provider.model == "text-embedding-3-small"
    assert isinstance(store, QdrantVectorStore)
    assert store._collection_name == "exobios_chunks"
    assert store._vector_size == provider.dimensions


def test_factory_initializes_the_collection_when_missing(fake_openai_client, fake_qdrant_client):
    settings = _settings(QDRANT_COLLECTION="brand_new_collection")

    build_default_embedding_service(
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

    build_default_embedding_service(
        settings=settings, openai_client=fake_openai_client, qdrant_client=fake_qdrant_client
    )

    assert fake_qdrant_client.created_collections == []


def test_factory_uses_configured_batch_size(fake_openai_client, fake_qdrant_client):
    settings = _settings(EMBEDDING_BATCH_SIZE=1)

    service = build_default_embedding_service(
        settings=settings, openai_client=fake_openai_client, qdrant_client=fake_qdrant_client
    )

    service._provider.embed_batch(["a", "b", "c"])

    assert fake_openai_client.calls == [["a"], ["b"], ["c"]]
