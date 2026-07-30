import pytest

from app.embeddings.exceptions import EmbeddingGenerationError
from app.embeddings.providers.openai_provider import OpenAIEmbeddingProvider
from tests.embeddings.conftest import FakeOpenAIClient


def test_embed_text_returns_a_single_vector(fake_openai_client):
    provider = OpenAIEmbeddingProvider(api_key="test-key", client=fake_openai_client)

    vector = provider.embed_text("hello")

    assert vector == [5.0] * fake_openai_client.dimensions
    assert fake_openai_client.calls == [["hello"]]


def test_embed_batch_returns_empty_list_without_calling_client(fake_openai_client):
    provider = OpenAIEmbeddingProvider(api_key="test-key", client=fake_openai_client)

    vectors = provider.embed_batch([])

    assert vectors == []
    assert fake_openai_client.calls == []


def test_embed_batch_splits_requests_at_configured_batch_size(fake_openai_client):
    provider = OpenAIEmbeddingProvider(api_key="test-key", batch_size=2, client=fake_openai_client)
    texts = ["a", "bb", "ccc", "dddd", "e"]

    vectors = provider.embed_batch(texts)

    assert len(vectors) == 5
    assert fake_openai_client.calls == [["a", "bb"], ["ccc", "dddd"], ["e"]]


def test_embed_batch_preserves_input_order():
    client = FakeOpenAIClient(dimensions=1)
    provider = OpenAIEmbeddingProvider(api_key="test-key", batch_size=100, client=client)

    vectors = provider.embed_batch(["a", "abc", "ab"])

    assert vectors == [[1.0], [3.0], [2.0]]


def test_embed_batch_raises_embedding_generation_error_on_client_failure():
    client = FakeOpenAIClient(fail_with=RuntimeError("upstream unavailable"))
    provider = OpenAIEmbeddingProvider(api_key="test-key", client=client)

    with pytest.raises(EmbeddingGenerationError):
        provider.embed_batch(["hello"])


def test_dimensions_property_for_known_model(fake_openai_client):
    provider = OpenAIEmbeddingProvider(
        api_key="test-key", model="text-embedding-3-small", client=fake_openai_client
    )

    assert provider.dimensions == 1536


def test_dimensions_property_falls_back_for_unknown_model(fake_openai_client):
    provider = OpenAIEmbeddingProvider(
        api_key="test-key", model="some-future-model", client=fake_openai_client
    )

    assert provider.dimensions == 1536


def test_model_property_reflects_configured_model(fake_openai_client):
    provider = OpenAIEmbeddingProvider(
        api_key="test-key", model="text-embedding-3-large", client=fake_openai_client
    )

    assert provider.model == "text-embedding-3-large"
