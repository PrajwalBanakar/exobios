# from enum import StrEnum
# from uuid import UUID

# from pydantic import BaseModel, ConfigDict, Field


# class ComplaintCategory(StrEnum):
#     FEVER = "FEVER"
#     RESPIRATORY = "RESPIRATORY"
#     GASTROINTESTINAL = "GASTROINTESTINAL"
#     MATERNAL_HEALTH = "MATERNAL_HEALTH"
#     CHILD_HEALTH = "CHILD_HEALTH"
#     SKIN = "SKIN"
#     MUSCULOSKELETAL = "MUSCULOSKELETAL"
#     NEUROLOGICAL = "NEUROLOGICAL"
#     CARDIOVASCULAR = "CARDIOVASCULAR"
#     MENTAL_HEALTH = "MENTAL_HEALTH"
#     OTHER = "OTHER"


# class SymptomSummary(BaseModel):
#     model_config = ConfigDict(extra="ignore")

#     name: str
#     duration: str | None = None
#     severity: str | None = None


# class VitalsSummary(BaseModel):
#     model_config = ConfigDict(extra="ignore", populate_by_name=True)

#     heart_rate: int | None = Field(default=None, alias="heartRate")
#     spo2: float | None = None
#     temperature: float | None = None
#     blood_pressure_systolic: int | None = Field(default=None, alias="bloodPressureSystolic")
#     blood_pressure_diastolic: int | None = Field(default=None, alias="bloodPressureDiastolic")
#     respiratory_rate: int | None = Field(default=None, alias="respiratoryRate")


# class AiRequest(BaseModel):
#     """Mirrors com.exobios.backend.integration.ai.AiRequest.

#     Optional fields must tolerate being entirely absent, not just null —
#     Jackson omits null fields on serialization. extra="ignore" keeps this
#     forward-compatible with backend changes.
#     """

#     model_config = ConfigDict(extra="ignore", populate_by_name=True)

#     assessment_id: UUID = Field(alias="assessmentId")
#     patient_id: UUID = Field(alias="patientId")
#     patient_complaint: str | None = Field(default=None, alias="patientComplaint")
#     complaint_category: ComplaintCategory | None = Field(default=None, alias="complaintCategory")
#     symptoms: list[SymptomSummary] = Field(default_factory=list)
#     vitals: VitalsSummary | None = None
#     past_illnesses: str | None = Field(default=None, alias="pastIllnesses")
#     current_medications: str | None = Field(default=None, alias="currentMedications")
#     allergies: str | None = None


from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ComplaintCategory(StrEnum):
    FEVER = "FEVER"
    RESPIRATORY = "RESPIRATORY"
    GASTROINTESTINAL = "GASTROINTESTINAL"
    MATERNAL_HEALTH = "MATERNAL_HEALTH"
    CHILD_HEALTH = "CHILD_HEALTH"
    SKIN = "SKIN"
    MUSCULOSKELETAL = "MUSCULOSKELETAL"
    NEUROLOGICAL = "NEUROLOGICAL"
    CARDIOVASCULAR = "CARDIOVASCULAR"
    MENTAL_HEALTH = "MENTAL_HEALTH"
    OTHER = "OTHER"


class SymptomSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    duration: str | None = None
    severity: str | None = None


class VitalsSummary(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    heart_rate: int | None = Field(default=None, alias="heartRate")
    spo2: float | None = None
    temperature: float | None = None
    blood_pressure_systolic: int | None = Field(default=None, alias="bloodPressureSystolic")
    blood_pressure_diastolic: int | None = Field(default=None, alias="bloodPressureDiastolic")
    respiratory_rate: int | None = Field(default=None, alias="respiratoryRate")
    # random blood sugar — sent by the assessment form (vitals.rbs), not in the
    # original Java DTO snapshot; optional so absence never breaks parsing.
    rbs: float | None = None


class AiRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    assessment_id: UUID = Field(alias="assessmentId")
    patient_id: UUID = Field(alias="patientId")
    patient_complaint: str | None = Field(default=None, alias="patientComplaint")
    complaint_category: ComplaintCategory | None = Field(default=None, alias="complaintCategory")
    symptoms: list[SymptomSummary] = Field(default_factory=list)
    vitals: VitalsSummary | None = None
    past_illnesses: str | None = Field(default=None, alias="pastIllnesses")
    current_medications: str | None = Field(default=None, alias="currentMedications")
    allergies: str | None = None
    age: int | None = None
    gender: str | None = None