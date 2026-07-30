from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.ingestion.models.chunk import Chunk, ChunkMetadata
from app.ingestion.models.document import DocumentMetadata, DocumentType


class FakeOpenAIClient:
    """Stands in for `openai.OpenAI`: only implements
    `.embeddings.create(model=, input=)`, mirroring the shape
    OpenAIEmbeddingProvider actually calls, with no network access."""

    def __init__(self, dimensions: int = 8, fail_with: Exception | None = None) -> None:
        self.dimensions = dimensions
        self.fail_with = fail_with
        self.calls: list[list[str]] = []
        self.embeddings = SimpleNamespace(create=self._create)

    def _create(self, model: str, input: list[str]):
        if self.fail_with is not None:
            raise self.fail_with
        self.calls.append(list(input))
        # Deterministic, distinguishable-by-length fake vectors — good enough
        # to assert shape/count without needing real embeddings.
        data = [SimpleNamespace(embedding=[float(len(text))] * self.dimensions) for text in input]
        return SimpleNamespace(data=data)


class FakeQdrantClient:
    """Stands in for `qdrant_client.QdrantClient`: implements only the
    methods QdrantVectorStore calls, with no network access."""

    def __init__(self, existing_collections: list[str] | None = None) -> None:
        self._collections = set(existing_collections or [])
        self.created_collections: list[tuple[str, object]] = []
        self.upserted: list[tuple[str, list]] = []
        self.deleted: list[tuple[str, object]] = []
        self.scroll_result: tuple[list, None] = ([], None)
        self.fail_with: Exception | None = None

    def get_collections(self):
        if self.fail_with is not None:
            raise self.fail_with
        names = [SimpleNamespace(name=name) for name in self._collections]
        return SimpleNamespace(collections=names)

    def create_collection(self, collection_name, vectors_config):
        if self.fail_with is not None:
            raise self.fail_with
        self._collections.add(collection_name)
        self.created_collections.append((collection_name, vectors_config))

    def upsert(self, collection_name, points):
        if self.fail_with is not None:
            raise self.fail_with
        self.upserted.append((collection_name, points))

    def delete(self, collection_name, points_selector):
        if self.fail_with is not None:
            raise self.fail_with
        self.deleted.append((collection_name, points_selector))

    def scroll(self, collection_name, scroll_filter, limit):
        if self.fail_with is not None:
            raise self.fail_with
        return self.scroll_result


@pytest.fixture
def fake_openai_client() -> FakeOpenAIClient:
    return FakeOpenAIClient()


@pytest.fixture
def fake_qdrant_client() -> FakeQdrantClient:
    return FakeQdrantClient()


def make_document_metadata(**overrides) -> DocumentMetadata:
    defaults = {
        "filename": "note.txt",
        "original_path": "/tmp/note.txt",
        "document_type": DocumentType.TXT,
        "source": "unit-test",
        "checksum": "checksum-" + uuid4().hex,
    }
    defaults.update(overrides)
    return DocumentMetadata(**defaults)


def make_chunk(document_id, chunk_number: int = 1, text: str = "hello world", **overrides) -> Chunk:
    metadata_defaults = {
        "document_id": document_id,
        "page_number": 1,
        "chunk_number": chunk_number,
        "start_offset": 0,
        "end_offset": len(text),
        "section_title": None,
    }
    metadata_defaults.update(overrides)
    return Chunk(text=text, metadata=ChunkMetadata(**metadata_defaults))
