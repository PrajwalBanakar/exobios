from pydantic import BaseModel, Field

from schemas.stages.deterministic_rule import Severity


class ImmediateMeasure(BaseModel):
    order: int
    action: str


class WarningSign(BaseModel):
    description: str
    detected: bool


class PlanOfActionResult(BaseModel):
    immediate_measures: list[ImmediateMeasure] = Field(default=[], serialization_alias="immediateMeasures")
    warning_signs: list[WarningSign] = Field(default=[], serialization_alias="warningSigns")
    risk_level: Severity = Field(default=Severity.LOW, serialization_alias="riskLevel")
    risk_floor_conflict: bool = Field(default=False, serialization_alias="riskFloorConflict")
    referral_advice: str | None = Field(default=None, serialization_alias="referralAdvice")
