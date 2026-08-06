# from pydantic import BaseModel
# from uuid import UUID
# from .state_object import StateObject

# class AssessmentResponse(BaseModel):
#     assessment_id: UUID
#     assesment: StateObject


from uuid import UUID

from pydantic import BaseModel

from schemas.stages.deterministic_rule import DeterministicRuleResult
from schemas.stages.diagnosis import DiagnosisResult
from schemas.stages.investigation import InvestigationResult
from schemas.stages.plan_of_action import PlanOfActionResult
from schemas.stages.treatment_protocol import TreatmentProtocolResult
from schemas.state_object import AssessmentState


class AssessmentResponse(BaseModel):
    assessment_id: UUID
    status: str = "COMPLETED"
    deterministic_flags: DeterministicRuleResult
    diagnosis: DiagnosisResult
    investigation: InvestigationResult
    treatment_protocol: TreatmentProtocolResult
    plan_of_action: PlanOfActionResult
    validation_flags: list[str] = []

    @classmethod
    def from_state(cls, state: AssessmentState) -> "AssessmentResponse":
        return cls(
            assessment_id=state.assessment_id,
            deterministic_flags=state.deterministic_flags,
            diagnosis=state.diagnosis,
            investigation=state.investigation,
            treatment_protocol=state.treatment_protocol,
            plan_of_action=state.plan_of_action,
            validation_flags=state.validation_flags,
        )