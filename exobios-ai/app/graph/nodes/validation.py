"""
Validation logic is written once (`validate_stage`) and wrapped into four
thin per-position node functions by `make_validation_node`, since LangGraph
registers nodes by graph position — but the actual checking logic is not
duplicated.

Citation verification (`_verify_and_filter_citations`) is the code-level
groundedness enforcement described in docs/ARCHITECTURE.md as a known gap:
prompts instruct the LLM to cite only retrieved excerpts, but nothing
previously checked that it actually did. Every citation an LLM stage returns
is now cross-checked against `state.retrieved_evidence[stage_name]` — the
literal chunks that were retrieved and shown to it. A citation whose
chunk_id was never retrieved is not trusted (it is dropped, and if that
verification is the LLM paraphrasing/altering wording, the original
retrieved text is substituted so downstream consumers always see the
authoritative source excerpt, never LLM-transcribed text). A candidate/test/
step left with zero verified citations is dropped entirely — an unsupported
claim must not reach the clinical response. If diagnosis ends up with no
verified candidates, insufficient_evidence is force-set to True in code,
independent of whether the LLM itself set that flag.
"""

from core.reporting import reporter
from repositories.persistence import persist_state
from schemas.stages.deterministic_rule import Severity
from schemas.step import StepResult, StepStatus

_STAGE_ITEM_ACCESSORS = {
    "diagnosis": lambda state: (state.diagnosis.candidates if state.diagnosis else []),
    "investigation": lambda state: (state.investigation.tests if state.investigation else []),
    "treatment_protocol": lambda state: (state.treatment_protocol.steps if state.treatment_protocol else []),
    "plan_of_action": lambda state: [],  # synthesis stage — no fresh citations to check
}


def _verify_and_filter_citations(state, stage_name: str) -> None:
    items = _STAGE_ITEM_ACCESSORS.get(stage_name, lambda s: [])(state)
    if not items:
        return

    retrieved_by_id = {c.chunk_id: c for c in state.retrieved_evidence.get(stage_name, [])}

    kept = []
    dropped_citations = 0
    empty_excerpts = 0
    for item in items:
        verified = []
        for citation in item.citations:
            source = retrieved_by_id.get(citation.chunk_id)
            if source is None:
                dropped_citations += 1
                continue
            verified.append(source)  # trust only the retrieved excerpt, not the LLM's echo of it
        if verified:
            item.citations = verified
            if any(not c.excerpt.strip() for c in verified):
                empty_excerpts += 1
            kept.append(item)

    dropped_items = len(items) - len(kept)
    if dropped_citations or dropped_items:
        state.validation_flags.append(
            f"{stage_name}: dropped {dropped_citations} unverifiable citation(s) whose chunk_id was "
            f"not among the chunks retrieved for this stage, and {dropped_items} item(s) left with "
            "no verified supporting evidence"
        )
    if empty_excerpts:
        state.validation_flags.append(f"{stage_name}: {empty_excerpts} item(s) cite a retrieved chunk with empty excerpt text")

    if stage_name == "diagnosis" and state.diagnosis:
        had_candidates = bool(state.diagnosis.candidates)
        state.diagnosis.candidates = kept
        if had_candidates and not kept:
            state.diagnosis.insufficient_evidence = True
            state.validation_flags.append(
                "diagnosis: all candidates were dropped during citation verification — "
                "forcing insufficient_evidence=True"
            )
    elif stage_name == "investigation" and state.investigation:
        state.investigation.tests = kept
    elif stage_name == "treatment_protocol" and state.treatment_protocol:
        state.treatment_protocol.steps = kept


def validate_stage(state, stage_name: str) -> None:
    _verify_and_filter_citations(state, stage_name)

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
