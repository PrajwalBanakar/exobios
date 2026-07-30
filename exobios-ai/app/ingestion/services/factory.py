from app.ingestion.chunkers.recursive_chunker import RecursiveChunker
from app.ingestion.cleaning.text_cleaner import TextCleaner
from app.ingestion.loaders.local_loader import LocalFileLoader
from app.ingestion.parsers.registry import ParserRegistry
from app.ingestion.registry.in_memory_registry import InMemoryDocumentRegistry
from app.ingestion.services.ingestion_service import IngestionService


def build_default_ingestion_service(
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> IngestionService:
    """Composition root for the default local-filesystem, in-memory-registry
    wiring. Callers needing different collaborators (e.g. a future S3 loader
    or PostgreSQL registry) should construct IngestionService directly.
    """
    return IngestionService(
        loader=LocalFileLoader(),
        parser_registry=ParserRegistry(),
        cleaner=TextCleaner(),
        chunker=RecursiveChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
        registry=InMemoryDocumentRegistry(),
    )
