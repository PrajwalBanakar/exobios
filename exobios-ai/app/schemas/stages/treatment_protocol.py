from pydantic import BaseModel, Field

from schemas.stages.common import SupportingCitation


class TreatmentStep(BaseModel):
    order: int
    instruction: str
    citations: list[SupportingCitation] = []


class TreatmentProtocolResult(BaseModel):
    steps: list[TreatmentStep] = []
    based_on_diagnosis: list[str] = Field(default=[], serialization_alias="basedOnDiagnosis")
    patient_factors_considered: list[str] = Field(default=[], serialization_alias="patientFactorsConsidered")
    regimen_specificity_flag: bool = Field(default=False, serialization_alias="regimenSpecificityFlag")
