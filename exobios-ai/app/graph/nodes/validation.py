"""
Validation logic is written once (`validate_stage`) and wrapped into four
thin per-position node functions by `make_validation_node`, since LangGraph
registers nodes by graph position — but the actual checking logic is not
duplicated.
"""

from core.reporting import reporter
from repositories.persistence import persist_state
from schemas.stages.deterministic_rule import Severity
from schemas.step import StepResult, StepStatus

_STAGE_CITATION_GETTERS = {
    "diagnosis": lambda state: [c for cand in (state.diagnosis.candidates if state.diagnosis else []) for c in cand.citations],
    "investigation": lambda state: [c for t in (state.investigation.tests if state.investigation else []) for c in t.citations],
    "treatment_protocol": lambda state: [c for s in (state.treatment_protocol.steps if state.treatment_protocol else []) for c in s.citations],
    "plan_of_action": lambda state: [],  # synthesis stage — no fresh citations to check
}


def validate_stage(state, stage_name: str) -> None:
    citations = _STAGE_CITATION_GETTERS.get(stage_name, lambda s: [])(state)

    empty_excerpts = [c for c in citations if not c.excerpt.strip()]
    if empty_excerpts:
        msg = f"{stage_name}: {len(empty_excerpts)} citation(s) with empty excerpt"
        state.validation_flags.append(msg)

    risk_floor = state.deterministic_flags.risk_floor if state.deterministic_flags else Severity.LOW
    if stage_name == "plan_of_action" and state.plan_of_action:
        rank = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2, Severity.CRITICAL: 3}
        if rank[state.plan_of_action.risk_level] < rank[risk_floor]:
            state.validation_flags.append("plan_of_action risk_level below risk_floor — should have been caught upstream")

    reporter.report(StepResult(
        step_name=f"validate:{stage_name}",
        status=StepStatus.SUCCESS,
        data={"issues_found": len([f for f in state.validation_flags if f.startswith(stage_name)])},
    ))


def make_validation_node(stage_name: str):
    def _node(state):
        validate_stage(state, stage_name)
        persist_state(state, stage_name)
        return state
    return _node