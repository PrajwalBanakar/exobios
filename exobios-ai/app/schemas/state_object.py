"""
the single state that will be manipulated by and shared across all the nodes

5 stages - 
    non over-rideable rules
    diff diagnosys
    recommended investigation
    treatment protocol
    plan of action

"""

from pydantic import BaseModel
from uuid import UUID
from .request import AiRequest
from .stages.deterministic_rule import DeterministicRuleResult
from .stages.diagnosis import DiagnosisResult
from .stages.investigation import InvestigationResult
from .stages.treatment_protocol import TreatmentProtocolResult
from .stages.plan_of_action import PlanOfActionResult

class StateObject(BaseModel):
    assessment_id: UUID
    patient_input: AiRequest
    deterministic_flags: DeterministicRuleResult | None = None
    diagnosis: DiagnosisResult | None = None
    investigation: InvestigationResult | None = None
    treatment_protocol: TreatmentProtocolResult | None = None
    plan_of_action: PlanOfActionResult | None = None
    # validation_flags: list[str] = []