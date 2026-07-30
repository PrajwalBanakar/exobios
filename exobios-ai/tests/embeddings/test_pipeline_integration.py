from pathlib import Path

import pytest

from app.embeddings.exceptions import EmbeddingGenerationError, VectorStoreError
from app.embeddings.providers.openai_provider import OpenAIEmbeddingProvider
from app.embeddings.services.embedding_service import EmbeddingService
from app.embeddings.vectorstores.qdrant_store import QdrantVectorStore
from app.ingestion.chunkers.recursive_chunker import RecursiveChunker
from app.ingestion.cleaning.text_cleaner import TextCleaner
from app.ingestion.loaders.local_loader import LocalFileLoader
from app.ingestion.models.document import DocumentStatus
from app.ingestion.parsers.registry import ParserRegistry
from app.ingestion.registry.in_memory_registry import InMemoryDocumentRegistry
from app.ingestion.services.ingestion_service import IngestionService


def _build_ingestion_service(
    fake_openai_client, fake_qdrant_client, chunk_size: int = 100, chunk_overlap: int = 10
) -> IngestionService:
    provider = OpenAIEmbeddingProvider(api_key="test-key", client=fake_openai_client)
    vector_store = QdrantVectorStore(
        client=fake_qdrant_client, collection_name="exobios_chunks", vector_size=provider.dimensions
    )
    vector_store.initialize()
    embedding_service = EmbeddingService(provider=provider, vector_store=vector_store)

    return IngestionService(
        loader=LocalFileLoader(),
        parser_registry=ParserRegistry(),
        cleaner=TextCleaner(),
        chunker=RecursiveChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
        registry=InMemoryDocumentRegistry(),
        embedding_service=embedding_service,
    )


def test_ingest_embeds_and_upserts_every_chunk_into_qdrant(
    tmp_path: Path, fake_openai_client, fake_qdrant_client
):
    file_path = tmp_path / "note.txt"
    file_path.write_text("Patient reports fever and cough.\n\n" * 50, encoding="utf-8")
    service = _build_ingestion_service(fake_openai_client, fake_qdrant_client)

    result = service.ingest(file_path, source="unit-test")

    assert result.document.status == DocumentStatus.COMPLETED
    assert len(fake_qdrant_client.upserted) == 1
    collection_name, points = fake_qdrant_client.upserted[0]
    assert collection_name == "exobios_chunks"
    assert len(points) == len(result.chunks) == result.document.chunk_count

    point_ids = {point.id for point in points}
    assert point_ids == {str(chunk.id) for chunk in result.chunks}
    for point in points:
        assert point.payload["document_id"] == str(result.document.id)
        assert point.payload["filename"] == "note.txt"
        assert point.payload["document_type"] == "TXT"


def test_ingest_collection_is_created_before_any_upsert(
    tmp_path: Path, fake_openai_client, fake_qdrant_client
):
    file_path = tmp_path / "note.txt"
    file_path.write_text("short note", encoding="utf-8")
    service = _build_ingestion_service(fake_openai_client, fake_qdrant_client)

    service.ingest(file_path, source="unit-test")

    assert len(fake_qdrant_client.created_collections) == 1
    assert len(fake_qdrant_client.upserted) == 1


def test_ingest_does_not_register_document_when_embedding_fails(tmp_path: Path, fake_qdrant_client):
    file_path = tmp_path / "note.txt"
    file_path.write_text("short note", encoding="utf-8")
    from tests.embeddings.conftest import FakeOpenAIClient

    failing_client = FakeOpenAIClient(fail_with=RuntimeError("rate limited"))
    service = _build_ingestion_service(failing_client, fake_qdrant_client)

    with pytest.raises(EmbeddingGenerationError):
        service.ingest(file_path, source="unit-test")

    assert fake_qdrant_client.upserted == []


def test_ingest_does_not_register_document_when_vector_store_upsert_fails(
    tmp_path: Path, fake_openai_client, fake_qdrant_client
):
    file_path = tmp_path / "note.txt"
    file_path.write_text("short note", encoding="utf-8")
    service = _build_ingestion_service(fake_openai_client, fake_qdrant_client)
    fake_qdrant_client.fail_with = RuntimeError("qdrant unreachable")

    with pytest.raises(VectorStoreError):
        service.ingest(file_path, source="unit-test")
