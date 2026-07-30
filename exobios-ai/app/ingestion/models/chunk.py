from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ChunkMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    page_number: int | None
    chunk_number: int
    # Character offsets into the cleaned text of the page identified by
    # page_number (not the whole document).
    start_offset: int
    end_offset: int
    section_title: str | None = None


class Chunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    text: str
    metadata: ChunkMetadata
