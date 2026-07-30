from pydantic import BaseModel, ConfigDict

from app.ingestion.models.chunk import Chunk


class EmbeddingVector(BaseModel):
    model_config = ConfigDict(extra="forbid")

    values: list[float]
    model: str
    dimensions: int


class EmbeddedChunk(BaseModel):
    """Pairs a Chunk with the vector generated for its text — the unit of
    work a VectorStore persists."""

    model_config = ConfigDict(extra="forbid")

    chunk: Chunk
    vector: EmbeddingVector
