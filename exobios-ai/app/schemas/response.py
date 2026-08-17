from uuid import UUID

from pydantic import BaseModel, Field

from config.settings import settings
from schemas.stages.deterministic_rule import DeterministicRuleResult
from schemas.stages.diagnosis import DiagnosisResult
from schemas.stages.investigation import InvestigationResult
from schemas.stages.plan_of_action import PlanOfActionResult
from schemas.stages.treatment_protocol import TreatmentProtocolResult
from schemas.state_object import AssessmentState

_SOURCE = "exobios-ai-langgraph"


class AssessmentResponse(BaseModel):
    """The `/analyze` response.

    Two things live in this one payload on purpose, not as separate
    endpoints, because Spring Boot's RestAiGateway only ever calls
    `/analyze` once per assessment:

    1. A flat, camelCase, top-level envelope (status/summary/riskLevel/
       confidenceScore/redFlags/recommendations/modelVersion/source) that is
       wire-compatible with the legacy `AiResponse` DTO documented in
       docs/api/ai-service-contract.md and consumed by
       `AssessmentService.callAiGateway`. Every one of those fields is
       mechanically derived from the real pipeline state below — nothing
       here is fabricated or LLM-generated specifically for this envelope.
    2. The full rich per-stage detail (deterministic_flags/diagnosis/
       investigation/treatment_protocol/plan_of_action/validation_flags),
       camelCase-aliased the same way, for any consumer that parses beyond
       the legacy top-level fields. Spring Boot's Jackson config
       (`fail-on-unknown-properties: false`) ignores these today without
       erroring — they are additive, not breaking.

    See docs/api/ai-service-contract.md for the full before/after and the
    2026-08 audit for why this shape was chosen over either discarding the
    rich detail or forcing a backend DTO/DB migration.
    """

    assessment_id: UUID = Field(serialization_alias="assessmentId")

    # ── Legacy-contract-compatible envelope ──────────────────────────────
    status: str = "COMPLETED"
    summary: str
    risk_level: str | None = Field(default=None, serialization_alias="riskLevel")
    confidence_score: float | None = Field(default=None, serialization_alias="confidenceScore")
    red_flags: str = Field(default="", serialization_alias="redFlags")
    recommendations: str = ""
    model_version: str = Field(default="", serialization_alias="modelVersion")
    source: str = _SOURCE

    # ── Full structured detail ───────────────────────────────────────────
    deterministic_flags: DeterministicRuleResult = Field(serialization_alias="deterministicFlags")
    diagnosis: DiagnosisResult
    investigation: InvestigationResult
    treatment_protocol: TreatmentProtocolResult = Field(serialization_alias="treatmentProtocol")
    plan_of_action: PlanOfActionResult = Field(serialization_alias="planOfAction")
    validation_flags: list[str] = Field(default=[], serialization_alias="validationFlags")

    @classmethod
    def from_state(cls, state: AssessmentState) -> "AssessmentResponse":
        return cls(
            assessment_id=state.assessment_id,
            summary=_build_summary(state),
            risk_level=state.plan_of_action.risk_level.value if state.plan_of_action else None,
            confidence_score=_top_confidence(state),
            red_flags=_build_red_flags(state),
            recommendations=_build_recommendations(state),
            model_version=settings.llm.model,
            deterministic_flags=state.deterministic_flags,
            diagnosis=state.diagnosis,
            investigation=state.investigation,
            treatment_protocol=state.treatment_protocol,
            plan_of_action=state.plan_of_action,
            validation_flags=state.validation_flags,
        )


def _top_confidence(state: AssessmentState) -> float | None:
    if not state.diagnosis or not state.diagnosis.candidates:
        return None
    return state.diagnosis.candidates[0].confidence_score


def _build_summary(state: AssessmentState) -> str:
    diagnosis = state.diagnosis
    if not diagnosis or not diagnosis.candidates or diagnosis.insufficient_evidence:
        return (
            "Insufficient evidence in the approved knowledge base to generate a "
            "differential diagnosis for this presentation."
        )
    top = diagnosis.candidates[0]
    risk = state.plan_of_action.risk_level.value if state.plan_of_action else "UNKNOWN"
    parts = [
        f"Top differential: {top.disease_name} ({top.confidence_label} confidence).",
        f"Risk level: {risk}.",
        f"{len(diagnosis.candidates)} candidate(s) considered.",
    ]
    if state.plan_of_action and state.plan_of_action.risk_floor_conflict:
        parts.append("Risk level was raised to match a deterministic safety threshold.")
    return " ".join(parts)


def _build_red_flags(state: AssessmentState) -> str:
    flags: list[str] = []
    if state.deterministic_flags:
        flags.extend(
            f"{f.code} ({f.threshold})" if f.threshold else f.code
            for f in state.deterministic_flags.flags
        )
    if state.plan_of_action:
        flags.extend(w.description for w in state.plan_of_action.warning_signs if w.detected)
        if state.plan_of_action.risk_floor_conflict:
            flags.append("AI-suggested risk level was overridden by a deterministic safety threshold")
    return "; ".join(flags)


def _build_recommendations(state: AssessmentState) -> str:
    if not state.plan_of_action:
        return ""
    parts = [m.action for m in sorted(state.plan_of_action.immediate_measures, key=lambda m: m.order)]
    if state.plan_of_action.referral_advice:
        parts.append(state.plan_of_action.referral_advice)
    return "; ".join(parts)
