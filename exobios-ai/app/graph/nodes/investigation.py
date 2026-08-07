"""
input is: differrential diagnosis from node 1
reads the diseases, does retrieval and rerank by hybrid search in QDrant against the diagnosed diseases
gets back citations/chunks from qdrant, llm call with the chunks payload
generated the recommended investigation object
write to the state object the recommended investigation object
also persist the state to db again

"""


from core.reporting import reporter
from graph.nodes.diagnosis import _format_citations
from graph.tools.retrieval import retrieve_and_rerank
from schemas.stages.investigation import InvestigationResult
from schemas.step import StepResult, StepStatus
from services.llm_service import llm_service

SYSTEM_PROMPT = """You are a clinical decision support assistant. Given a
diagnosed/suspected condition, recommend confirmatory investigations, using
ONLY the retrieved excerpts as your evidence base. Every test must cite the
excerpt that justifies it. Respond only with JSON matching the given schema."""


def investigation_node(state):
    if not state.diagnosis or not state.diagnosis.candidates:
        state.investigation = _empty_investigation()
        return state

    disease_names = [c.disease_name for c in state.diagnosis.candidates[:3]]
    query = " ".join(f"{name} diagnostic test confirmation method" for name in disease_names)
    filters = {"complaint_category": state.patient_input.complaint_category.value} if state.patient_input.complaint_category else {}

    citations = retrieve_and_rerank(query, filters, top_k=8)

    user_prompt = f"""
Suspected conditions (ranked): {', '.join(disease_names)}

Retrieved clinical excerpts on confirmatory investigations:
{_format_citations(citations)}

Recommend investigations with urgency (URGENT/HIGH/MEDIUM/LOW), rationale,
and citations for each. Set based_on_diagnosis to {disease_names}.
"""

    result: InvestigationResult = llm_service.generate_structured(SYSTEM_PROMPT, user_prompt, InvestigationResult)
    result.based_on_diagnosis = disease_names
    state.investigation = result

    reporter.report(StepResult(
        step_name="investigation",
        status=StepStatus.SUCCESS,
        data={"num_tests": len(result.tests)},
    ))
    return state


def _empty_investigation() -> InvestigationResult:
    return InvestigationResult(tests=[], based_on_diagnosis=[])