from pydantic import BaseModel
from document_schema import DocumentMetadata
from chunk_schema import ChunkPayload
from uuid import UUID

class PayLoad(BaseModel):
    document_payload: DocumentMetadata
    chunk_payload: ChunkPayload

class MetadataPayload(BaseModel):
    id: UUID
    payload: PayLoad
    