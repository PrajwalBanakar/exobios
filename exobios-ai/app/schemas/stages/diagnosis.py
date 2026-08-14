from pydantic import BaseModel, Field

from schemas.stages.common import SupportingCitation


class DiagnosisCandidate(BaseModel):
    disease_name: str = Field(serialization_alias="diseaseName")
    confidence_score: float = Field(serialization_alias="confidenceScore")
    confidence_label: str = Field(serialization_alias="confidenceLabel")
    supporting_evidence: list[str] = Field(default=[], serialization_alias="supportingEvidence")
    citations: list[SupportingCitation] = []
    reasoning: str


class DiagnosisResult(BaseModel):
    candidates: list[DiagnosisCandidate] = []
    query_used: str = Field(default="", serialization_alias="queryUsed")
    insufficient_evidence: bool = Field(default=False, serialization_alias="insufficientEvidence")
