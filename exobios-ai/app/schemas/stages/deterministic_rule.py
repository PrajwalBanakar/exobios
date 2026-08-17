from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DeterministicFlag(BaseModel):
    code: str
    severity: Severity
    value: float | int | None = None
    threshold: str | None = None


class DeterministicRuleResult(BaseModel):
    flags: list[DeterministicFlag] = []
    # Values are identical to Java's RiskLevel enum literals (LOW/MEDIUM/HIGH/
    # CRITICAL) — no translation needed at the contract boundary.
    risk_floor: Severity = Field(default=Severity.LOW, serialization_alias="riskFloor")