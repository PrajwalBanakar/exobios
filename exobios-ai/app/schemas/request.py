"""Mirrors com.exobios.backend.integration.ai.AiRequest.

Optional fields must tolerate being entirely absent, not just null —
Jackson omits null fields on serialization. extra="ignore" keeps this
forward-compatible with backend changes.
"""

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

    # Bounds below are physiological plausibility limits only (a heart rate
    # can't be negative; SpO2 can't exceed 100%) — not clinical thresholds.
    # They exist so a bad upstream value (unit error, sensor fault, typo)
    # fails request validation instead of silently flowing into the
    # deterministic rule engine and downstream LLM prompts unchecked.
    heart_rate: int | None = Field(default=None, alias="heartRate", ge=0, le=300)
    spo2: float | None = Field(default=None, ge=0, le=100)
    # Fahrenheit — matches the frontend (labeled "(°F)" throughout) and this
    # service's own rule_engine.py thresholds (104/102, unambiguously
    # Fahrenheit). 86-113 mirrors exobios-backend's VitalsRequest.temperature
    # bound exactly (see its doc comment for the mathematical-conversion
    # rationale) so a value accepted/rejected by one layer is never silently
    # treated differently by the other — see the 2026-08 audit's Priority 2.
    temperature: float | None = Field(default=None, ge=86, le=113)
    blood_pressure_systolic: int | None = Field(default=None, alias="bloodPressureSystolic", ge=0, le=300)
    blood_pressure_diastolic: int | None = Field(default=None, alias="bloodPressureDiastolic", ge=0, le=250)
    respiratory_rate: int | None = Field(default=None, alias="respiratoryRate", ge=0, le=100)
    # random blood sugar — sent by the assessment form (vitals.rbs), not in the
    # original Java DTO snapshot; optional so absence never breaks parsing.
    rbs: float | None = Field(default=None, ge=0, le=1000)


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
    age: int | None = Field(default=None, ge=0, le=130)
    gender: str | None = None
