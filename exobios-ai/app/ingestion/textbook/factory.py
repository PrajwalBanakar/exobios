from google import genai
from openai import OpenAI
from qdrant_client import QdrantClient

from app.core.config import Settings, get_settings
from app.embeddings.factory import build_default_embedding_provider_and_store
from app.ingestion.registry.interface import DocumentRegistry
from app.ingestion.registry.sqlite_registry import SQLiteDocumentRegistry
from app.ingestion.textbook.artifacts import TextbookArtifactWriter
from app.ingestion.textbook.chunker import TextbookChunker
from app.ingestion.textbook.embedding_ingestion import TextbookEmbeddingIngestionService
from app.ingestion.textbook.page_extractor import TextbookPageExtractor
from app.ingestion.textbook.service import TextbookPreparationService
from app.storage.interface import DocumentStorage
from app.storage.local_storage import LocalDocumentStorage


def build_default_textbook_preparation_service(
    settings: Settings | None = None,
    registry: DocumentRegistry | None = None,
    storage: DocumentStorage | None = None,
) -> TextbookPreparationService:
    """Composition root wiring the default local/SQLite collaborators into a
    TextbookPreparationService. `registry`/`storage` are injectable so tests
    (and a future AI-7C wiring a different registry/storage backend) can
    supply alternatives without changing this function's callers.
    """
    settings = settings or get_settings()
    registry = registry or SQLiteDocumentRegistry(
        db_path=settings.document_registry_db_path_resolved
    )
    storage = storage or LocalDocumentStorage(root=settings.document_storage_root_path)

    extractor = TextbookPageExtractor()
    chunker = TextbookChunker(
        target_tokens=settings.textbook_chunk_target_tokens,
        max_tokens=settings.textbook_chunk_max_tokens,
        overlap_tokens=settings.textbook_chunk_overlap_tokens,
        min_useful_tokens=settings.textbook_min_chunk_tokens,
    )
    artifact_writer = TextbookArtifactWriter(
        extracted_root=settings.document_extracted_root_path,
        processed_root=settings.document_processed_root_path,
    )

    return TextbookPreparationService(
        registry=registry,
        storage=storage,
        extractor=extractor,
        chunker=chunker,
        artifact_writer=artifact_writer,
    )


def build_default_textbook_embedding_ingestion_service(
    settings: Settings | None = None,
    registry: DocumentRegistry | None = None,
    openai_client: OpenAI | None = None,
    gemini_client: genai.Client | None = None,
    qdrant_client: QdrantClient | None = None,
) -> TextbookEmbeddingIngestionService:
    """Composition root for AI-7C's embedding ingestion: reads AI-7B's
    chunks.jsonl via TextbookArtifactWriter, embeds via whichever provider
    is configured (matching app.embeddings.factory's own OpenAI/Gemini
    selection — same helper, so the two never disagree), and stores into
    `settings.qdrant_textbook_collection` (isolated from the IMNCI demo's
    `qdrant_collection`).
    """
    settings = settings or get_settings()
    registry = registry or SQLiteDocumentRegistry(
        db_path=settings.document_registry_db_path_resolved
    )
    artifact_reader = TextbookArtifactWriter(
        extracted_root=settings.document_extracted_root_path,
        processed_root=settings.document_processed_root_path,
    )
    provider, vector_store = build_default_embedding_provider_and_store(
        settings=settings,
        openai_client=openai_client,
        gemini_client=gemini_client,
        qdrant_client=qdrant_client,
        collection_name=settings.qdrant_textbook_collection,
    )

    return TextbookEmbeddingIngestionService(
        registry=registry,
        artifact_reader=artifact_reader,
        embedding_provider=provider,
        vector_store=vector_store,
        embedding_batch_size=settings.embedding_batch_size,
    )
