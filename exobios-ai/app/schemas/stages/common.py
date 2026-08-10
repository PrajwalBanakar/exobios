from pydantic import BaseModel


class SupportingCitation(BaseModel):
    chunk_id: str
    document_id: str
    excerpt: str
    heading: str
    page: int