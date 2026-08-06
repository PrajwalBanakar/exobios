from datetime import datetime, timezone

from core.exceptions import PersistenceException
from core.reporting import reporter
from repositories import assessment_repository
from schemas.state_object import AssessmentState
from schemas.step_result import StepResult, StepStatus
from .assesment import upsert_assessment

def persist_state(state: AssessmentState, stage_name: str) -> None:
    """One Mongo document per assessment (per user's decision — unstructured,
    single doc, updated in place). Each call overwrites the whole current
    state snapshot plus records which stage last ran and when, so an
    assessment can be reopened at any point without replaying the graph."""
    try:
        assessment_repository.upsert_assessment(
            str(state.assessment_id),
            {
                "assessment_id": str(state.assessment_id),
                "patient_input": state.patient_input.model_dump(mode="json"),
                "deterministic_flags": _dump(state.deterministic_flags),
                "diagnosis": _dump(state.diagnosis),
                "investigation": _dump(state.investigation),
                "treatment_protocol": _dump(state.treatment_protocol),
                "plan_of_action": _dump(state.plan_of_action),
                "validation_flags": state.validation_flags,
                "last_stage": stage_name,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        reporter.report(StepResult(
            step_name=f"persist:{stage_name}",
            status=StepStatus.SUCCESS,
            data={"assessment_id": str(state.assessment_id)},
        ))
    except Exception as e:
        reporter.report(StepResult(
            step_name=f"persist:{stage_name}",
            status=StepStatus.FAIL,
            error_message=str(e),
        ))
        raise PersistenceException(str(e))


def _dump(obj) -> dict | None:
    return obj.model_dump(mode="json") if obj is not None else None