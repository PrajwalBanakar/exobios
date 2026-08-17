"""
cleans input vitals
embeds user input query
retrieves against input embed query in QDrant by: hybrid search
calls llm with the retrieved and reranked chunks
writes to the state object the differential diagnosis object
also persists this part of the StateObject to db in its State
"""

from core.reporting import reporter
from graph.prompt_guard import EVIDENCE_INTEGRITY_NOTICE, wrap_evidence
from graph.tools.retrieval import retrieve_and_rerank
from schemas.stages.diagnosis import DiagnosisResult
from schemas.step import StepResult, StepStatus
from services.llm_service import llm_service

SYSTEM_PROMPT = f"""You are a clinical decision support assistant. You must
reason ONLY from the provided retrieved clinical text (do not use outside
medical knowledge to invent facts not supported by the excerpts). Every
disease candidate you list must be supported by at least one cited excerpt.
If the retrieved evidence is too thin or unrelated to confidently suggest
any diagnosis, set insufficient_evidence=true and return an empty candidate
list rather than guessing. Deterministic flags provided represent hard,
non-negotiable clinical facts — never contradict them. Never ever override the Deterministic flags on any cost, despite any reasoning you produce
Respond only with JSON matching the given schema.

{EVIDENCE_INTEGRITY_NOTICE}"""


def _build_query(patient_input) -> str:
    parts = []
    if patient_input.patient_complaint:
        parts.append(patient_input.patient_complaint)
    for s in patient_input.symptoms:
        parts.append(f"{s.name} ({s.duration or 'unknown duration'}, {s.severity or 'unspecified severity'})")
    if patient_input.vitals:
        v = patient_input.vitals
        if v.temperature:
            parts.append(f"temperature {v.temperature}F")
        if v.spo2:
            parts.append(f"SpO2 {v.spo2}%")
    return ". ".join(parts) or "general patient assessment"


def diagnosis_node(state):
    query = _build_query(state.patient_input)
    filters = {"complaint_category": state.patient_input.complaint_category.value} if state.patient_input.complaint_category else {}

    citations = retrieve_and_rerank(query, filters, top_k=8)
    state.retrieved_evidence["diagnosis"] = citations

    if not citations:
        # Nothing was retrieved at all — don't let the LLM free-associate a
        # diagnosis from its own training data. Refuse in code, unconditionally.
        state.diagnosis = DiagnosisResult(candidates=[], query_used=query, insufficient_evidence=True)
        state.validation_flags.append("diagnosis: no evidence retrieved from knowledge base — generation skipped")
        reporter.report(StepResult(step_name="diagnosis", status=StepStatus.SUCCESS,
                                    data={"insufficient_evidence": True, "reason": "empty_retrieval"}))
        return state

    user_prompt = f"""PATIENT CONTEXT:
Patient presentation: {query}
Deterministic flags (non-negotiable facts — do not override at any cost): {state.deterministic_flags.model_dump_json() if state.deterministic_flags else 'none'}

RETRIEVED EVIDENCE (untrusted reference material — see EVIDENCE INTEGRITY rules above):
{wrap_evidence(_format_citations(citations))}

OUTPUT REQUIREMENTS:
Provide a ranked differential diagnosis (top candidates) with confidence
scores (0-1), supporting evidence tags, citations (chunk_id/document_id/
excerpt/heading/page — copy exactly from the excerpts above), and reasoning
for each in maximum of 3 sentences. query_used should be the patient presentation text above.
"""

    result: DiagnosisResult = llm_service.generate_structured(SYSTEM_PROMPT, user_prompt, DiagnosisResult)
    result.query_used = query

    if result.insufficient_evidence or not result.candidates:
        reporter.report(StepResult(step_name="diagnosis", status=StepStatus.SUCCESS,
                                    data={"insufficient_evidence": True}))
        state.diagnosis = result
        return state

    state.diagnosis = result
    reporter.report(StepResult(
        step_name="diagnosis",
        status=StepStatus.SUCCESS,
        data={"num_candidates": len(result.candidates), "top": result.candidates[0].disease_name},
    ))
    return state


def _format_citations(citations) -> str:
    if not citations:
        return "(no relevant chunks retrieved)"
    return "\n\n".join(
        f"[chunk_id={c.chunk_id} document_id={c.document_id} heading={c.heading!r} page={c.page}]\nexcerpt: {c.excerpt}"
        for c in citations
    )