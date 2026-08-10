# from pydantic import BaseModel
# from enum import StrEnum

# class Severity(StrEnum):
#     LOW = "LOW"
#     MEDIUM = "MEDIUM"
#     HIGH = "HIGH"
#     CRITICAL = "CRITICAL"

# class DeterministicFlag(BaseModel):
#     code: str              # "OXYGEN_SATURATION_ABNORMAL"
#     severity: Severity
#     value: float | int | None = None
#     threshold: str | None = None   # human-readable, e.g. "< 90%"

# class DeterministicRuleResult(BaseModel):
#     flags: list[DeterministicFlag]
#     risk_floor: Severity           # the non-negotiable floor every later stage must respect

from enum import StrEnum

from pydantic import BaseModel


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
    risk_floor: Severity = Severity.LOW