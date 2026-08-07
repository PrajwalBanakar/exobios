"""
no db search, feed all stages: diagnosis, investigation, treatment
generate using all these via an llm
maybe look into the qdrant if any treatment protocol is there
manipulate state, 
persist the state to db

"""


from core.reporting import reporter
from schemas.stages.deterministic_rule import Severity
from schemas.stages.plan_of_action import PlanOfActionResult
from schemas.step import StepResult, StepStatus
from services.llm_service import llm_service

SYSTEM_PROMPT = """You are a clinical decision support assistant. Synthesize
a plan of action from the diagnosis, investigations, and treatment already
produced, plus deterministic safety flags. Do NOT search for new evidence —
reason only over what is given. The deterministic risk_floor is a hard,
non-negotiable floor: risk_level in your output must never be lower than
risk_floor, and if risk_floor is CRITICAL, immediate_measures must include
urgent referral/escalation regardless of what the treatment protocol
suggests. Respond only with JSON matching the given schema."""


def _severity_rank(s: Severity) -> int:
    return {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2, Severity.CRITICAL: 3}[s]


def plan_of_action_node(state):
    risk_floor = state.deterministic_flags.risk_floor if state.deterministic_flags else Severity.LOW

    user_prompt = f"""
Diagnosis: {state.diagnosis.model_dump_json() if state.diagnosis else 'none'}
Investigations: {state.investigation.model_dump_json() if state.investigation else 'none'}
Treatment protocol: {state.treatment_protocol.model_dump_json() if state.treatment_protocol else 'none'}
Deterministic flags: {state.deterministic_flags.model_dump_json() if state.deterministic_flags else 'none'}
risk_floor (hard minimum): {risk_floor.value}
"""

    result: PlanOfActionResult = llm_service.generate_structured(SYSTEM_PROMPT, user_prompt, PlanOfActionResult)

    # enforce the floor in code too — never trust the LLM alone for this
    if _severity_rank(result.risk_level) < _severity_rank(risk_floor):
        result.risk_floor_conflict = True
        result.risk_level = risk_floor

    state.plan_of_action = result
    if result.risk_floor_conflict:
        state.validation_flags.append("plan_of_action risk_level was overridden to match deterministic risk_floor")

    reporter.report(StepResult(
        step_name="plan_of_action",
        status=StepStatus.SUCCESS,
        data={"risk_level": result.risk_level.value, "conflict": result.risk_floor_conflict},
    ))
    return state