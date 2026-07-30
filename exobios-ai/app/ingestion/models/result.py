from pydantic import BaseModel, ConfigDict

from app.ingestion.models.chunk import Chunk
from app.ingestion.models.document import DocumentMetadata


class IngestionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document: DocumentMetadata
    chunks: list[Chunk]
