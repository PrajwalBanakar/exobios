from pydantic import BaseModel
from enum import StrEnum

class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    
    
# all of below filled by AI wrt the citations

class ImmediateMeasure(BaseModel):
    order: int
    action: str

class WarningSign(BaseModel):
    description: str
    detected: bool

class PlanOfActionResult(BaseModel):
    immediate_measures: list[ImmediateMeasure]
    warning_signs: list[WarningSign]
    risk_level: RiskLevel                  # must equal deterministic_flags.risk_floor at minimum
    # risk_floor_conflict: bool               # True if LLM synthesis disagreed with deterministic flags — logged, never surfaced as the final answer
    referral_advice: str | None = None