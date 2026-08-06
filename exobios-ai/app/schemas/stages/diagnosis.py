# """
# disease categories -> [names (linked ids of registered names)]
# [disease names]
# for every name -> [ids of pulled supporting citations [chunks], confidence score, AI reasoning]

# """

# from pydantic import BaseModel
# from uuid import UUID

# class SupportingCitation(BaseModel):
#     chunk_id: UUID
#     document_id: str
#     excerpt: str | None = None # can be pulled from QDrant on demand
#     heading: str
#     page_start: int
#     page_end: int
    

# class DiagnosisCandidate(BaseModel):
#     disease_name: str
#     icd10_code: str | None = None
#     confidence_score: float          
#     confidence_label: str            
#     # supporting_evidence: list[str]
#     citations: list[SupportingCitation]
#     reasoning: str                  

# class DiagnosisResult(BaseModel):
#     candidates: list[DiagnosisCandidate]   
#     input_query: str                         


from pydantic import BaseModel

from schemas.stages.common import SupportingCitation


class DiagnosisCandidate(BaseModel):
    disease_name: str
    confidence_score: float
    confidence_label: str
    supporting_evidence: list[str] = []
    citations: list[SupportingCitation] = []
    reasoning: str


class DiagnosisResult(BaseModel):
    candidates: list[DiagnosisCandidate] = []
    query_used: str = ""
    insufficient_evidence: bool = False