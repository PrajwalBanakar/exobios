"""End-to-end verification scenarios (Priority 12 of the 2026-08 Phase 2
audit) — as far as this environment allows.

No Docker daemon / live Qdrant / live MongoDB is reachable in this
environment (verified during the audit), so these are NOT live-infrastructure
tests: they run the REAL LangGraph pipeline (rule_engine -> diagnosis ->
investigation -> treatment_protocol -> plan_of_action -> validation ->
citation verification) through the real /analyze route, with Qdrant/HF/Groq/
Mongo mocked at the service-call boundary (see conftest.py). This proves the
pipeline's own logic — grounding, citation verification, the deterministic
risk floor, failure propagation — is correct. It does NOT prove a live
external provider behaves as mocked. See the audit report for what remains
unverified against real infrastructure.
"""

import uuid

from tests.conftest import MOCK_CHUNK_ID, MOCK_DOCUMENT_ID


def _body(**overrides) -> dict:
    base = {"assessmentId": str(uuid.uuid4()), "patientId": str(uuid.uuid4()), "symptoms": []}
    base.update(overrides)
    return base


def _auth(api_key: str) -> dict:
    return {"X-Api-Key": api_key}


# ── Test A: relevant case — retrieval finds real evidence, response is grounded ──


def test_scenario_a_relevant_case_produces_grounded_verified_response(client, api_key):
    body = _body(
        patientComplaint="High fever and rash for 4 days",
        complaintCategory="FEVER",
        vitals={"heartRate": 92, "spo2": 97, "temperature": 101.5},
    )
    response = client.post("/analyze", json=body, headers=_auth(api_key))

    assert response.status_code == 200
    data = response.json()

    # Retrieval occurred and citations exist.
    candidates = data["diagnosis"]["candidates"]
    assert len(candidates) >= 1
    citation = candidates[0]["citations"][0]

    # Citations correspond to real (mocked-as-retrieved) chunks, not
    # fabricated ones — this is the citation-verification guarantee.
    assert citation["chunkId"] == MOCK_CHUNK_ID
    assert citation["documentId"] == MOCK_DOCUMENT_ID

    # Backend-compatible top-level fields are populated from real state, not a placeholder.
    assert data["status"] == "COMPLETED"
    assert data["source"] == "exobios-ai-langgraph"
    assert data["source"] != "exobios-ai-unavailable"
    assert data["summary"]
    assert "insufficient evidence" not in data["summary"].lower()


# ── Test B: insufficient evidence — must refuse, not manufacture an answer ──


def test_scenario_b_insufficient_evidence_refuses_rather_than_fabricates(client, api_key, monkeypatch):
    from graph.nodes import diagnosis as diagnosis_module
    from schemas.stages.diagnosis import DiagnosisResult
    from tests.conftest import fake_generate_structured

    def _diagnosis_llm_must_not_be_called(system_prompt, user_prompt, response_schema):
        # diagnosis must skip its LLM call entirely when nothing was
        # retrieved (that's the code-enforced refusal being tested) — but
        # plan_of_action still legitimately runs afterwards regardless of
        # diagnosis's outcome, so only diagnosis's call is disallowed here.
        if response_schema is DiagnosisResult:
            raise AssertionError("LLM must not be called for diagnosis when nothing was retrieved")
        return fake_generate_structured(system_prompt, user_prompt, response_schema)

    monkeypatch.setattr(diagnosis_module, "retrieve_and_rerank", lambda *a, **k: [])
    monkeypatch.setattr(diagnosis_module.llm_service, "generate_structured", _diagnosis_llm_must_not_be_called)

    body = _body(patientComplaint="An intentionally unsupported, off-topic query about spacecraft engines")
    response = client.post("/analyze", json=body, headers=_auth(api_key))

    assert response.status_code == 200
    data = response.json()

    assert data["diagnosis"]["insufficientEvidence"] is True
    assert data["diagnosis"]["candidates"] == []
    assert data["confidenceScore"] is None
    assert "insufficient evidence" in data["summary"].lower()
    assert data["status"] == "COMPLETED"  # a refusal is a valid completed outcome, not a system failure


# ── Test C: deterministic red flag — the LLM cannot lower the risk floor ──


def test_scenario_c_deterministic_red_flag_cannot_be_lowered_by_the_llm(client, api_key):
    # SpO2 85% trips rule_engine.py's EXISTING SPO2_CRITICAL threshold
    # (< 90%) -> risk_floor = CRITICAL. No new threshold invented here.
    body = _body(vitals={"spo2": 85})
    response = client.post("/analyze", json=body, headers=_auth(api_key))

    assert response.status_code == 200
    data = response.json()

    assert data["deterministicFlags"]["riskFloor"] == "CRITICAL"
    flag_codes = [f["code"] for f in data["deterministicFlags"]["flags"]]
    assert "SPO2_CRITICAL" in flag_codes

    # The mocked LLM's plan_of_action response defaults to LOW (see
    # conftest.py's fake_generate_structured) — the code must force it up
    # to CRITICAL regardless, and record that it did.
    assert data["riskLevel"] == "CRITICAL"
    assert data["planOfAction"]["riskLevel"] == "CRITICAL"
    assert data["planOfAction"]["riskFloorConflict"] is True
    assert any("risk_floor" in f.lower() or "override" in f.lower() for f in data["validationFlags"])
    assert "SPO2_CRITICAL" in data["redFlags"]


# ── Test D: dependency failure — explicit failure, never a fabricated result ──


def test_scenario_d_qdrant_failure_returns_explicit_error_not_a_fabricated_result(client, api_key, monkeypatch):
    from services import qdrant_service as qdrant_module
    from core.exceptions import RetrievalException

    def _boom(*a, **k):
        raise RetrievalException("qdrant hybrid search failed: connection refused")

    monkeypatch.setattr(qdrant_module.qdrant_service, "hybrid_search", _boom)

    response = client.post("/analyze", json=_body(), headers=_auth(api_key))

    assert response.status_code == 502
    body = response.json()
    assert body["error_code"] == "retrieval_failed"
    assert "request_id" in body
    # Explicitly not a 200 with a plausible-looking clinical result.
    assert "riskLevel" not in body
    assert "diagnosis" not in body


def test_scenario_d_llm_failure_returns_explicit_error_not_a_fabricated_result(client, api_key, monkeypatch):
    from services import llm_service as llm_module
    from core.exceptions import LLMGenerationException

    def _boom(*a, **k):
        raise LLMGenerationException("groq call failed: 500 Internal Server Error")

    monkeypatch.setattr(llm_module.llm_service, "generate_structured", _boom)

    response = client.post("/analyze", json=_body(), headers=_auth(api_key))

    assert response.status_code == 502
    body = response.json()
    assert body["error_code"] == "llm_generation_failed"
    assert "riskLevel" not in body
