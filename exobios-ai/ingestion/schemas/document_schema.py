from pydantic import BaseModel
from typing import List
class DocumentMetadata(BaseModel):
    document_id: str
    document_title: str
#   document_issuing_authority: str
#   version: str
#   publication_date: date
    complaint_category: str
    applicable_roles: List[str]
    file_location: str
#    content_hash: str