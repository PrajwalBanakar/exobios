import uuid

from tests.conftest import MOCK_CHUNK_ID


def _body(**overrides) -> dict:
    base = {
        "assessmentId": str(uuid.uuid4()),
        "patientId": str(uuid.uuid4()),
        "symptoms": [],
    }
    base.update(overrides)
    return base


def _auth_headers(api_key: str) -> dict:
    return {"X-Api-Key": api_key}


# ── Request validation ────────────────────────────────────────────────────────


def test_full_backend_compatible_request_is_accepted(client, api_key):
    body = _body(
        patientComplaint="Fever for 3 days",
        complaintCategory="FEVER",
        symptoms=[{"name": "cough", "duration": "3 days", "severity": "mild"}],
        vitals={
            "heartRate": 88,
            "spo2": 97.5,
            # Fahrenheit — the rule engine's own thresholds (rule_engine.py:
            # HYPERPYREXIA >= 104, HIGH_FEVER >= 102) and the frontend's
            # inputs (labeled "(°F)" throughout) are both Fahrenheit-scaled.
            "temperature": 100.8,
            "bloodPressureSystolic": 120,
            "bloodPressureDiastolic": 80,
            "respiratoryRate": 18,
        },
        pastIllnesses="None",
        currentMedications="None",
        allergies="None",
    )
    response = client.post("/analyze", json=body, headers=_auth_headers(api_key))
    assert response.status_code == 200


def test_nullable_optional_fields_accepted_when_absent(client, api_key):
    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    assert response.status_code == 200


def test_nullable_optional_fields_accepted_when_explicitly_null(client, api_key):
    body = _body(
        patientComplaint=None,
        complaintCategory=None,
        vitals=None,
        pastIllnesses=None,
        currentMedications=None,
        allergies=None,
    )
    response = client.post("/analyze", json=body, headers=_auth_headers(api_key))
    assert response.status_code == 200


def test_malformed_assessment_id_uuid_rejected(client, api_key):
    body = _body(assessmentId="not-a-uuid")
    response = client.post("/analyze", json=body, headers=_auth_headers(api_key))
    assert response.status_code == 422


def test_malformed_patient_id_uuid_rejected(client, api_key):
    body = _body(patientId="not-a-uuid")
    response = client.post("/analyze", json=body, headers=_auth_headers(api_key))
    assert response.status_code == 422


def test_missing_required_field_rejected(client, api_key):
    body = _body()
    del body["assessmentId"]
    response = client.post("/analyze", json=body, headers=_auth_headers(api_key))
    assert response.status_code == 422


def test_invalid_complaint_category_rejected(client, api_key):
    body = _body(complaintCategory="NOT_A_REAL_CATEGORY")
    response = client.post("/analyze", json=body, headers=_auth_headers(api_key))
    assert response.status_code == 422


def test_invalid_nested_symptom_data_rejected(client, api_key):
    body = _body(symptoms=[{"name": 12345}])
    response = client.post("/analyze", json=body, headers=_auth_headers(api_key))
    assert response.status_code == 422


def test_symptom_missing_required_name_rejected(client, api_key):
    body = _body(symptoms=[{"duration": "3 days"}])
    response = client.post("/analyze", json=body, headers=_auth_headers(api_key))
    assert response.status_code == 422


def test_invalid_vitals_type_rejected(client, api_key):
    body = _body(vitals={"heartRate": "not-a-number"})
    response = client.post("/analyze", json=body, headers=_auth_headers(api_key))
    assert response.status_code == 422


def test_malformed_json_body_handled_safely(client, api_key):
    response = client.post(
        "/analyze",
        content="{not valid json",
        headers={**_auth_headers(api_key), "Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert "Traceback" not in response.text


# ── Vitals bounds (physiological plausibility, not clinical thresholds) ───────


def test_physiologically_impossible_heart_rate_rejected(client, api_key):
    body = _body(vitals={"heartRate": -5})
    response = client.post("/analyze", json=body, headers=_auth_headers(api_key))
    assert response.status_code == 422


def test_spo2_over_100_percent_rejected(client, api_key):
    body = _body(vitals={"spo2": 150})
    response = client.post("/analyze", json=body, headers=_auth_headers(api_key))
    assert response.status_code == 422


def test_temperature_bound_matches_backend_vitalsrequest_exactly(client, api_key):
    # 70F is physiologically-plausible-adjacent (a prior, wider AI-side-only
    # bound of 60-115 would have accepted it) but is now rejected because it
    # sits outside exobios-backend's VitalsRequest.temperature bound
    # (86-113F) — the two layers must agree on what's rejected, not each
    # enforce a different range for the same field. See the 2026-08 audit's
    # Priority 2 (temperature unit fix).
    body = _body(vitals={"temperature": 70})
    response = client.post("/analyze", json=body, headers=_auth_headers(api_key))
    assert response.status_code == 422


def test_plausible_extreme_vitals_still_accepted(client, api_key):
    # SpO2 88 is a real, dangerous, clinically-plausible value — must not be
    # rejected by request validation; it's the rule engine's job (not the
    # schema's) to flag it as a danger sign.
    body = _body(vitals={"spo2": 88, "heartRate": 140})
    response = client.post("/analyze", json=body, headers=_auth_headers(api_key))
    assert response.status_code == 200


# ── Response shape (current AssessmentState/AssessmentResponse contract) ──────
#
# NOTE: docs/api/ai-service-contract.md documents a different, flatter
# `AiResponse` shape (status/summary/riskLevel/confidenceScore/redFlags/
# recommendations/modelVersion/source) that exobios-backend's RestAiGateway
# actually deserializes into. That contract describes the AI-1 placeholder
# phase and was never updated for the LangGraph pipeline implemented here —
# see the production-readiness audit for details. These tests assert the
# response this codebase actually produces today. As of the Phase 2
# contract-alignment pass, the response is camelCase and its top-level keys
# are wire-compatible with the legacy AiResponse (status/summary/riskLevel/
# confidenceScore/redFlags/recommendations/modelVersion/source) that
# RestAiGateway deserializes into, PLUS the full rich per-stage detail
# alongside it (also camelCase) — see schemas/response.py's docstring.


def test_response_top_level_is_legacy_contract_compatible(client, api_key):
    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    data = response.json()
    legacy_contract_fields = {
        "status", "summary", "riskLevel", "confidenceScore",
        "redFlags", "recommendations", "modelVersion", "source",
    }
    assert legacy_contract_fields.issubset(data.keys())


def test_response_full_shape_includes_rich_detail_camelcase(client, api_key):
    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    data = response.json()
    assert set(data.keys()) == {
        "assessmentId", "status", "summary", "riskLevel", "confidenceScore",
        "redFlags", "recommendations", "modelVersion", "source",
        "deterministicFlags", "diagnosis", "investigation",
        "treatmentProtocol", "planOfAction", "validationFlags",
    }


def test_response_status_is_completed(client, api_key):
    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    assert response.json()["status"] == "COMPLETED"


def test_response_risk_level_matches_plan_of_action_and_java_enum_literal(client, api_key):
    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    data = response.json()
    assert data["riskLevel"] == data["planOfAction"]["riskLevel"]
    assert data["riskLevel"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def test_response_confidence_score_is_a_json_number_not_string(client, api_key):
    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    data = response.json()
    assert isinstance(data["confidenceScore"], (int, float))


def test_response_summary_is_not_fabricated_when_grounded(client, api_key):
    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    data = response.json()
    # Summary must be built from the real top candidate, not a canned string.
    assert data["diagnosis"]["candidates"][0]["diseaseName"] in data["summary"]


def test_response_diagnosis_citation_is_verified_against_retrieval(client, api_key):
    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    data = response.json()
    candidates = data["diagnosis"]["candidates"]
    assert len(candidates) == 1
    assert candidates[0]["citations"][0]["chunkId"] == MOCK_CHUNK_ID


def test_response_summary_and_confidence_are_honest_on_insufficient_evidence(client, api_key, monkeypatch):
    from graph.nodes import diagnosis as diagnosis_module

    monkeypatch.setattr(diagnosis_module, "retrieve_and_rerank", lambda *a, **k: [])

    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    data = response.json()
    assert data["diagnosis"]["insufficientEvidence"] is True
    assert data["confidenceScore"] is None
    assert "insufficient evidence" in data["summary"].lower()


# ── Middleware and errors ─────────────────────────────────────────────────────


def test_request_id_generated_when_absent(client):
    response = client.get("/health")
    assert response.headers.get("x-request-id")


def test_request_id_propagated_when_provided(client):
    custom_id = "test-request-id-123"
    response = client.get("/health", headers={"X-Request-Id": custom_id})
    assert response.headers["x-request-id"] == custom_id


def test_request_id_header_matches_id_used_for_the_request(client, api_key):
    # Regression test: api/routes/analyze.py used to overwrite the
    # request-scoped id with assessment_id mid-request, so the X-Request-Id
    # response header and the id used in server-side logs for the same
    # request would diverge. The header is the only externally-observable
    # signal of that id, so assert it's present and stable, not overwritten
    # to something request-body-dependent.
    custom_id = "trace-abc-123"
    response = client.post("/analyze", json=_body(), headers={**_auth_headers(api_key), "X-Request-Id": custom_id})
    assert response.headers["x-request-id"] == custom_id


def test_internal_error_does_not_expose_internals(client, api_key, monkeypatch):
    # analyze.py imports assessment_graph directly (`from graph.builder import
    # assessment_graph`), so patch the route module's own reference, not
    # graph.builder's — `analyze_module.assessment_graph` is a separate name
    # bound to the same object, and analyze() calls the name in its own
    # module's namespace.
    from api.routes import analyze as analyze_module

    def _boom(initial_state):
        raise RuntimeError("boom - /etc/secret-path")

    monkeypatch.setattr(analyze_module.assessment_graph, "invoke", _boom)

    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))

    assert response.status_code == 500
    text = response.text
    assert "Traceback" not in text
    assert "/etc/secret-path" not in text
    assert "boom" not in text
    assert "request_id" in response.json()
