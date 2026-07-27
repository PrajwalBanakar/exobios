from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Enum literals below must mirror the Java enums exactly (case-sensitive):
#   com.exobios.backend.assessments.entity.enums.ComplaintCategory
#   com.exobios.backend.assessments.entity.enums.RiskLevel
#   com.exobios.backend.assessments.entity.enums.AiResultStatus


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


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AiResultStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SymptomSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    duration: str | None = None
    severity: str | None = None


class VitalsSummary(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    heart_rate: int | None = Field(default=None, alias="heartRate")
    # Java's `spo2`/`temperature` are BigDecimal, but Pydantic v2 serializes
    # Decimal to a JSON *string* by default, which a Java BigDecimal field
    # would not deserialize as a number. `float` round-trips as a plain JSON
    # number, matching what Jackson expects on the wire.
    spo2: float | None = None
    temperature: float | None = None
    blood_pressure_systolic: int | None = Field(default=None, alias="bloodPressureSystolic")
    blood_pressure_diastolic: int | None = Field(default=None, alias="bloodPressureDiastolic")
    respiratory_rate: int | None = Field(default=None, alias="respiratoryRate")


class AiRequest(BaseModel):
    """Mirrors com.exobios.backend.integration.ai.AiRequest exactly.

    The Java side omits null fields from JSON (Jackson non_null inclusion), so
    every optional field here must tolerate being entirely absent, not just null.
    Unknown fields are ignored to stay forward-compatible with the backend.
    """

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


class AiResponse(BaseModel):
    """Mirrors com.exobios.backend.integration.ai.AiResponse exactly.

    FastAPI serializes response models using these aliases by default
    (response_model_by_alias defaults to True), producing the same camelCase
    JSON keys Jackson expects on deserialization.
    """

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    status: AiResultStatus
    summary: str | None = None
    risk_level: RiskLevel | None = Field(default=None, alias="riskLevel")
    # See VitalsSummary note above: float, not Decimal, so this serializes as
    # a JSON number that Java's BigDecimal-typed confidenceScore can deserialize.
    confidence_score: float | None = Field(default=None, alias="confidenceScore")
    red_flags: str | None = Field(default=None, alias="redFlags")
    recommendations: str | None = None
    model_version: str | None = Field(default=None, alias="modelVersion")
    source: str | None = None
