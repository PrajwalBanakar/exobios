"""Unit tests for the code-level groundedness enforcement added to
app/graph/nodes/validation.py and app/graph/nodes/diagnosis.py: an LLM
citation is only trusted if its chunk_id was actually retrieved for that
stage, and diagnosis with zero retrieved evidence never reaches the LLM at
all. These are the core patient-safety behaviors from the production audit —
"the AI should refuse rather than fabricate when evidence is missing."
"""

from uuid import uuid4

from graph.nodes.diagnosis import diagnosis_node
from graph.nodes.validation import validate_stage
from schemas.request import AiRequest
from schemas.stages.common import SupportingCitation
from schemas.stages.diagnosis import DiagnosisCandidate, DiagnosisResult
from schemas.state_object import AssessmentState


def _state(**diagnosis_kwargs) -> AssessmentState:
    patient_input = AiRequest(assessmentId=uuid4(), patientId=uuid4(), symptoms=[])
    state = AssessmentState(assessment_id=patient_input.assessment_id, patient_input=patient_input)
    if diagnosis_kwargs:
        state.diagnosis = DiagnosisResult(**diagnosis_kwargs)
    return state


def _real_citation(chunk_id: str) -> SupportingCitation:
    return SupportingCitation(chunk_id=chunk_id, document_id="doc-1", excerpt="real retrieved text", heading="h", page=1)


def test_citation_matching_retrieved_chunk_is_kept_and_canonicalized():
    real = _real_citation("chunk-real")
    # The LLM echoed back a slightly different excerpt for the same chunk_id —
    # verification must replace it with the authoritative retrieved text.
    llm_echoed = SupportingCitation(chunk_id="chunk-real", document_id="doc-1", excerpt="LLM's paraphrase of the text", heading="h", page=1)
    state = _state(candidates=[DiagnosisCandidate(disease_name="X", confidence_score=0.5, confidence_label="MEDIUM", citations=[llm_echoed], reasoning="r")])
    state.retrieved_evidence["diagnosis"] = [real]

    validate_stage(state, "diagnosis")

    assert len(state.diagnosis.candidates) == 1
    assert state.diagnosis.candidates[0].citations[0].excerpt == "real retrieved text"


def test_citation_not_in_retrieved_pool_is_dropped_as_hallucinated():
    real = _real_citation("chunk-real")
    fabricated = SupportingCitation(chunk_id="chunk-does-not-exist", document_id="doc-1", excerpt="made up", heading="h", page=1)
    state = _state(candidates=[
        DiagnosisCandidate(disease_name="Real", confidence_score=0.5, confidence_label="MEDIUM", citations=[real], reasoning="r"),
        DiagnosisCandidate(disease_name="Fabricated", confidence_score=0.9, confidence_label="HIGH", citations=[fabricated], reasoning="r"),
    ])
    state.retrieved_evidence["diagnosis"] = [real]

    validate_stage(state, "diagnosis")

    remaining = [c.disease_name for c in state.diagnosis.candidates]
    assert remaining == ["Real"]
    assert any("dropped" in f and "diagnosis" in f for f in state.validation_flags)


def test_all_candidates_hallucinated_forces_insufficient_evidence():
    fabricated = SupportingCitation(chunk_id="not-retrieved", document_id="doc-1", excerpt="made up", heading="h", page=1)
    state = _state(candidates=[
        DiagnosisCandidate(disease_name="Fabricated", confidence_score=0.9, confidence_label="HIGH", citations=[fabricated], reasoning="r"),
    ], insufficient_evidence=False)
    state.retrieved_evidence["diagnosis"] = []  # nothing retrieved at all for this stage

    validate_stage(state, "diagnosis")

    assert state.diagnosis.candidates == []
    assert state.diagnosis.insufficient_evidence is True


def test_diagnosis_node_skips_llm_and_refuses_when_nothing_retrieved(monkeypatch):
    from graph.nodes import diagnosis as diagnosis_module

    monkeypatch.setattr(diagnosis_module, "retrieve_and_rerank", lambda *a, **k: [])

    def _llm_should_not_be_called(*a, **k):
        raise AssertionError("LLM must not be called when retrieval returned nothing")

    monkeypatch.setattr(diagnosis_module.llm_service, "generate_structured", _llm_should_not_be_called)

    state = _state()
    result_state = diagnosis_node(state)

    assert result_state.diagnosis.insufficient_evidence is True
    assert result_state.diagnosis.candidates == []
