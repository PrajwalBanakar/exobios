from pydantic import BaseModel
from enum import StrEnum
from .diagnosis import SupportingCitation

class DiagnosedDiseases(BaseModel):
    disease_name: str
    icd10_code: str 

class UrgencyLevel(StrEnum):
    URGENT = "URGENT"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class RecommendedTest(BaseModel):     # ai generated against the pulled chunks
    test_name: str
    urgency: UrgencyLevel
    rationale: str                   # "Check platelet count and WBC for dengue confirmation"
    citations: list[SupportingCitation]

class InvestigationResult(BaseModel):
    tests: list[RecommendedTest]
    diagnosed_diseases: list[DiagnosedDiseases]     # disease names this was queried against