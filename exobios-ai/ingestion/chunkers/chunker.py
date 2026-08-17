"""
for every dd stored in drive accessed via its link ->
produce appropriate chunks using hybrid chunker
also produce tokens using docling's tokeniser for the embedding model being used
stream these into the embedding model
"""

import uuid
from typing import List

import tiktoken
from docling.chunking import HybridChunker
from docling_core.types.doc import DoclingDocument

from config.settings import settings
from core.reporting import reporter
from exceptions import ChunkingException
from schemas.chunk_schema import ChunkMetadata
from schemas.step_result import StepResult, StepStatus

from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer

encoding = tiktoken.get_encoding("cl100k_base")

tokenizer = OpenAITokenizer(
    tokenizer=encoding,
    max_tokens=settings.chunk_max_tokens,
)

chunker = HybridChunker(
    tokenizer=tokenizer,
    max_tokens=settings.chunk_max_tokens,
)


# Fixed namespace for deriving chunk ids — do not change; changing it would
# make every future ingestion run generate different chunk ids for identical
# documents/positions, defeating the idempotency this exists for.
_CHUNK_ID_NAMESPACE = uuid.UUID("6f5b1f8a-7c2e-4e3a-9c1d-2f6b0a2d9e11")


def _build_chunk_metadata(chunk, document_id: str, index: int) -> ChunkMetadata:
    headings = chunk.meta.headings if chunk.meta.headings else []
    heading = headings[-1] if headings else ""
    section = headings[0] if headings else ""

    pages = [
        prov.page_no
        for item in chunk.meta.doc_items
        for prov in item.prov
    ] if chunk.meta.doc_items else []

    page_start = min(pages) if pages else 0
    page_end = max(pages) if pages else 0

    # Deterministic, not uuid4(): derived from (document_id, position in the
    # document). Re-ingesting the same document — e.g. after a crash, or a
    # deliberate re-run — reproduces the same chunk ids, so the Qdrant
    # upsert in store/qdrant_store.py overwrites the existing points instead
    # of creating duplicates alongside them.
    chunk_id = uuid.uuid5(_CHUNK_ID_NAMESPACE, f"{document_id}:{index}")

    return ChunkMetadata(
        ingestion_version=settings.ingestion_version,
        chunk_id=chunk_id,
        page_start=page_start,
        page_end=page_end,
        content=chunk.text,
        section=section,
        heading=heading,
    )


def chunk_docling_document(docling_doc: DoclingDocument, document_id: str) -> List[ChunkMetadata]:
    try:
        raw_chunks = list(chunker.chunk(docling_doc))
        enriched_chunks = [_build_chunk_metadata(c, document_id, i) for i, c in enumerate(raw_chunks)]

    except ChunkingException as e:
        reporter.report(StepResult(
            step_name="chunking",
            status=StepStatus.FAIL,
            error_message=str(e),
        ))
        return []

    reporter.report(StepResult(
        step_name="chunking",
        status=StepStatus.SUCCESS,
        data={
            "document_id": document_id,
            "num_chunks": len(enriched_chunks),
            "message": f"Successfully chunked document {document_id} into {len(enriched_chunks)} chunks.",
        },
    ))
    
    return enriched_chunks