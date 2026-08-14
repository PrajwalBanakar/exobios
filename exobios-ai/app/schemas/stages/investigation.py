from enum import StrEnum

from pydantic import BaseModel, Field

from schemas.stages.common import SupportingCitation


class UrgencyLevel(StrEnum):
    URGENT = "URGENT"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RecommendedTest(BaseModel):
    test_name: str = Field(serialization_alias="testName")
    urgency: UrgencyLevel
    rationale: str
    citations: list[SupportingCitation] = []


class InvestigationResult(BaseModel):
    tests: list[RecommendedTest] = []
    based_on_diagnosis: list[str] = Field(default=[], serialization_alias="basedOnDiagnosis")
