import pytest

from app.embeddings.exceptions import EmbeddingGenerationError, VectorStoreError
from app.embeddings.services.embedding_service import EmbeddingService
from tests.embeddings.conftest import make_chunk, make_document_metadata


class FakeProvider:
    def __init__(self, dimensions: int = 4, fail_with: Exception | None = None) -> None:
        self._dimensions = dimensions
        self.fail_with = fail_with
        self.batches: list[list[str]] = []

    @property
    def model(self) -> str:
        return "fake-model"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_text(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self.fail_with is not None:
            raise self.fail_with
        self.batches.append(list(texts))
        return [[float(len(text))] * self._dimensions for text in texts]


class FakeVectorStore:
    def __init__(self, fail_with: Exception | None = None) -> None:
        self.fail_with = fail_with
        self.upserts: list[tuple] = []

    def initialize(self) -> None:
        pass

    def upsert_chunks(self, document, embedded_chunks) -> None:
        if self.fail_with is not None:
            raise self.fail_with
        self.upserts.append((document, embedded_chunks))

    def delete_document(self, document_id) -> None:
        pass

    def document_exists(self, document_id) -> bool:
        return False

    def health(self) -> bool:
        return True


def test_embed_document_generates_vectors_and_upserts_them():
    provider = FakeProvider()
    store = FakeVectorStore()
    service = EmbeddingService(provider=provider, vector_store=store)
    document = make_document_metadata()
    chunks = [
        make_chunk(document.id, chunk_number=1, text="a"),
        make_chunk(document.id, chunk_number=2, text="bb"),
    ]

    count = service.embed_document(document, chunks)

    assert count == 2
    assert provider.batches == [["a", "bb"]]
    assert len(store.upserts) == 1
    upserted_document, embedded_chunks = store.upserts[0]
    assert upserted_document is document
    assert [ec.chunk for ec in embedded_chunks] == chunks
    assert embedded_chunks[0].vector.values == [1.0] * provider.dimensions
    assert embedded_chunks[0].vector.model == "fake-model"


def test_embed_document_returns_zero_and_skips_upsert_for_no_chunks():
    provider = FakeProvider()
    store = FakeVectorStore()
    service = EmbeddingService(provider=provider, vector_store=store)
    document = make_document_metadata()

    count = service.embed_document(document, [])

    assert count == 0
    assert provider.batches == []
    assert store.upserts == []


def test_embed_document_propagates_embedding_generation_error():
    provider = FakeProvider(fail_with=EmbeddingGenerationError(reason="rate limited"))
    store = FakeVectorStore()
    service = EmbeddingService(provider=provider, vector_store=store)
    document = make_document_metadata()

    with pytest.raises(EmbeddingGenerationError):
        service.embed_document(document, [make_chunk(document.id)])

    assert store.upserts == []


def test_embed_document_wraps_unexpected_provider_exception():
    provider = FakeProvider(fail_with=RuntimeError("network error"))
    store = FakeVectorStore()
    service = EmbeddingService(provider=provider, vector_store=store)
    document = make_document_metadata()

    with pytest.raises(EmbeddingGenerationError):
        service.embed_document(document, [make_chunk(document.id)])


def test_embed_document_propagates_vector_store_error():
    provider = FakeProvider()
    store = FakeVectorStore(fail_with=VectorStoreError(reason="qdrant down"))
    service = EmbeddingService(provider=provider, vector_store=store)
    document = make_document_metadata()

    with pytest.raises(VectorStoreError):
        service.embed_document(document, [make_chunk(document.id)])


def test_embed_document_wraps_unexpected_store_exception():
    provider = FakeProvider()
    store = FakeVectorStore(fail_with=RuntimeError("disk full"))
    service = EmbeddingService(provider=provider, vector_store=store)
    document = make_document_metadata()

    with pytest.raises(VectorStoreError):
        service.embed_document(document, [make_chunk(document.id)])
