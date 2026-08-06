"""
Deterministic rule engine — plain code, no LLM, no retrieval. Runs first.
Thresholds below are commonly-cited public danger-sign values (WHO/IMNCI-style
vital sign ranges) — a placeholder set adequate for pipeline testing, not a
substitute for client-supplied/clinically-reviewed thresholds.
"""

from core.reporting import reporter
from schemas.request import AiRequest
from schemas.stages.deterministic_rule import DeterministicFlag, DeterministicRuleResult, Severity
from schemas.step_result import StepResult, StepStatus


def _severity_rank(s: Severity) -> int:
    return {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2, Severity.CRITICAL: 3}[s]


def evaluate_rules(patient_input: AiRequest) -> DeterministicRuleResult:
    flags: list[DeterministicFlag] = []
    v = patient_input.vitals

    if v is not None:
        if v.spo2 is not None:
            if v.spo2 < 90:
                flags.append(DeterministicFlag(code="SPO2_CRITICAL", severity=Severity.CRITICAL, value=v.spo2, threshold="< 90%"))
            elif v.spo2 < 94:
                flags.append(DeterministicFlag(code="SPO2_LOW", severity=Severity.HIGH, value=v.spo2, threshold="90-93%"))

        if v.temperature is not None:
            if v.temperature >= 104:
                flags.append(DeterministicFlag(code="HYPERPYREXIA", severity=Severity.CRITICAL, value=v.temperature, threshold=">= 104F"))
            elif v.temperature >= 102:
                flags.append(DeterministicFlag(code="HIGH_FEVER", severity=Severity.HIGH, value=v.temperature, threshold=">= 102F"))

        if v.heart_rate is not None:
            if v.heart_rate > 130 or v.heart_rate < 40:
                flags.append(DeterministicFlag(code="HEART_RATE_CRITICAL", severity=Severity.CRITICAL, value=v.heart_rate))
            elif v.heart_rate > 110 or v.heart_rate < 50:
                flags.append(DeterministicFlag(code="HEART_RATE_ABNORMAL", severity=Severity.HIGH, value=v.heart_rate))

        if v.respiratory_rate is not None:
            # adult default bands; a pediatric-age-banded version needs
            # patient_input.age wired through client-supplied norms
            if v.respiratory_rate > 30 or v.respiratory_rate < 8:
                flags.append(DeterministicFlag(code="RESPIRATORY_RATE_CRITICAL", severity=Severity.CRITICAL, value=v.respiratory_rate))
            elif v.respiratory_rate > 24 or v.respiratory_rate < 12:
                flags.append(DeterministicFlag(code="RESPIRATORY_RATE_ABNORMAL", severity=Severity.HIGH, value=v.respiratory_rate))

        if v.blood_pressure_systolic is not None:
            if v.blood_pressure_systolic < 90:
                flags.append(DeterministicFlag(code="HYPOTENSION", severity=Severity.CRITICAL, value=v.blood_pressure_systolic, threshold="< 90 mmHg systolic"))
            elif v.blood_pressure_systolic >= 180:
                flags.append(DeterministicFlag(code="HYPERTENSIVE_URGENCY", severity=Severity.HIGH, value=v.blood_pressure_systolic, threshold=">= 180 mmHg systolic"))

        if v.rbs is not None:
            if v.rbs < 54:
                flags.append(DeterministicFlag(code="HYPOGLYCEMIA", severity=Severity.CRITICAL, value=v.rbs, threshold="< 54 mg/dL"))
            elif v.rbs > 400:
                flags.append(DeterministicFlag(code="SEVERE_HYPERGLYCEMIA", severity=Severity.CRITICAL, value=v.rbs, threshold="> 400 mg/dL"))

    risk_floor = Severity.LOW
    for f in flags:
        if _severity_rank(f.severity) > _severity_rank(risk_floor):
            risk_floor = f.severity

    return DeterministicRuleResult(flags=flags, risk_floor=risk_floor)


def rule_engine_node(state):
    result = evaluate_rules(state.patient_input)
    state.deterministic_flags = result
    reporter.report(StepResult(
        step_name="rule_engine",
        status=StepStatus.SUCCESS,
        data={"num_flags": len(result.flags), "risk_floor": result.risk_floor.value},
    ))
    return state