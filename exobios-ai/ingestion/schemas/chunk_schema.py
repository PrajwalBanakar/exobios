from pydantic import BaseModel
from typing import List
from datetime import date
from uuid import UUID
# from './document_schema.py' import 
class ChunkMetadata(BaseModel):
    ingestion_version: str
    chunk_id: UUID
    page_start: int
    page_end: int
    # warning_chunk: bool
    content: str
    section: str
    heading: str

class VectorRecord(BaseModel):
    id: str
    vector: List[float]
    
class ChunkPayload(BaseModel):
    vector_record: VectorRecord
    chunk_metadata: ChunkMetadata