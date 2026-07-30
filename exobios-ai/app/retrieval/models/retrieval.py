from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.ingestion.models.document import DocumentType


class RetrievedChunk(BaseModel):
    """A single semantically-matched chunk, denormalized with enough of its
    parent document's metadata to be useful on its own."""

    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    chunk_id: UUID
    score: float
    text: str
    page_number: int | None
    section_title: str | None
    document_type: DocumentType
    filename: str
    language: str | None
    tags: list[str]
    version: str
    source: str


class SearchResult(BaseModel):
    """Raw output of a Retriever — the candidate set before reranking."""

    model_config = ConfigDict(extra="forbid")

    chunks: list[RetrievedChunk]


class SearchRequest(BaseModel):
    """Input to RetrievalService.search(). Overrides are optional — omitted
    fields fall back to the service's configured defaults."""

    model_config = ConfigDict(extra="forbid")

    query: str
    top_k: int | None = None
    min_score: float | None = None
    max_returned_chunks: int | None = None


class SearchResponse(BaseModel):
    """Final output of RetrievalService.search()."""

    model_config = ConfigDict(extra="forbid")

    query: str
    results: list[RetrievedChunk]
    result_count: int
    elapsed_ms: float = Field(ge=0)
