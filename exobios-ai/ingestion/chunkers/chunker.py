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
from schemas.step import StepResult, StepStatus

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


def _build_chunk_metadata(chunk) -> ChunkMetadata:
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

    return ChunkMetadata(
        ingestion_version=settings.ingestion_version,
        chunk_id=uuid.uuid4(),
        page_start=page_start,
        page_end=page_end,
        content=chunk.text,
        section=section,
        heading=heading,
    )


def chunk_docling_document(docling_doc: DoclingDocument, document_id: str) -> List[ChunkMetadata]:
    try:
        raw_chunks = list(chunker.chunk(docling_doc))
        enriched_chunks = [_build_chunk_metadata(c) for c in raw_chunks]

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
    
    print("\n" * 5)
    for c in enriched_chunks:
        print(c)
        print("\n" * 2)
    return enriched_chunks