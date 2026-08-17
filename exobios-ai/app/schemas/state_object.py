"""The single state manipulated by and shared across all graph nodes.

5 stages - non-overrideable rules, differential diagnosis, recommended
investigation, treatment protocol, plan of action.
"""

from uuid import UUID

from pydantic import BaseModel

from schemas.request import AiRequest
from schemas.stages.common import SupportingCitation
from schemas.stages.deterministic_rule import DeterministicRuleResult
from schemas.stages.diagnosis import DiagnosisResult
from schemas.stages.investigation import InvestigationResult
from schemas.stages.plan_of_action import PlanOfActionResult
from schemas.stages.treatment_protocol import TreatmentProtocolResult


class AssessmentState(BaseModel):
    assessment_id: UUID
    patient_input: AiRequest

    deterministic_flags: DeterministicRuleResult | None = None

    diagnosis: DiagnosisResult | None = None
    investigation: InvestigationResult | None = None
    treatment_protocol: TreatmentProtocolResult | None = None
    plan_of_action: PlanOfActionResult | None = None

    validation_flags: list[str] = []

    # The exact chunks retrieved+reranked for each stage, keyed by stage name
    # (e.g. "diagnosis"). This is the ground truth the validation node checks
    # LLM-returned citations against — an LLM citation whose chunk_id is not
    # in this pool for its stage was not actually retrieved, and is treated
    # as unverifiable/hallucinated rather than trusted. See graph/nodes/validation.py.
    retrieved_evidence: dict[str, list[SupportingCitation]] = {}