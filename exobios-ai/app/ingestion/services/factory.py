from app.embeddings.services.embedding_service import EmbeddingService
from app.ingestion.chunkers.recursive_chunker import RecursiveChunker
from app.ingestion.cleaning.text_cleaner import TextCleaner
from app.ingestion.loaders.local_loader import LocalFileLoader
from app.ingestion.parsers.registry import ParserRegistry
from app.ingestion.registry.in_memory_registry import InMemoryDocumentRegistry
from app.ingestion.services.ingestion_service import IngestionService


def build_default_ingestion_service(
    embedding_service: EmbeddingService,
    *,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> IngestionService:
    """Composition root for the default local-filesystem, in-memory-registry
    wiring. `embedding_service` is required (not defaulted) since building one
    means either reaching out to OpenAI/Qdrant or deliberately choosing a test
    double — callers should not get that silently for free. Callers needing
    different collaborators (e.g. a future S3 loader or PostgreSQL registry)
    should construct IngestionService directly.
    """
    return IngestionService(
        loader=LocalFileLoader(),
        parser_registry=ParserRegistry(),
        cleaner=TextCleaner(),
        chunker=RecursiveChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
        registry=InMemoryDocumentRegistry(),
        embedding_service=embedding_service,
    )
