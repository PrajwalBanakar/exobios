from pydantic import BaseModel
from .investigation import DiagnosedDiseases
from .diagnosis import SupportingCitation


class PatientFactors(BaseModel):
    # age, pregnancy, severity
    pass

class TreatmentStep(BaseModel):
    order: int
    instruction: str                 # "Paracetamol 650mg every 6 hours (avoid aspirin/ibuprofen in suspected dengue)"
    citations: list[SupportingCitation]

class TreatmentProtocolResult(BaseModel):
    steps: list[TreatmentStep]
    diagnosed_diseases: list[DiagnosedDiseases]
    patient_factors_considered: list[PatientFactors]   # age, pregnancy, severity — what the query was narrowed by
    # regimen_specificity_flag: bool           # True if patient factors weren't clearly matched — the uncertainty flag we discussed