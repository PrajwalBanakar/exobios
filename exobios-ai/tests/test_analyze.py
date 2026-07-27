import uuid


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
            "temperature": 38.2,
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


# ── Response shape ────────────────────────────────────────────────────────────


def test_response_matches_ai_response_shape(client, api_key):
    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    data = response.json()
    assert set(data.keys()) == {
        "status",
        "summary",
        "riskLevel",
        "confidenceScore",
        "redFlags",
        "recommendations",
        "modelVersion",
        "source",
    }


def test_response_status_is_java_compatible_enum_value(client, api_key):
    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    data = response.json()
    assert data["status"] in {"PENDING", "PROCESSING", "COMPLETED", "FAILED"}


def test_response_risk_level_is_null_not_fabricated(client, api_key):
    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    data = response.json()
    assert data["riskLevel"] is None


def test_response_confidence_score_is_contract_compatible(client, api_key):
    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    data = response.json()
    assert isinstance(data["confidenceScore"], (int, float))


def test_response_contains_no_fabricated_red_flags_or_recommendations(client, api_key):
    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    data = response.json()
    assert data["redFlags"] == ""
    assert data["recommendations"] == ""


def test_response_summary_discloses_stub_status(client, api_key):
    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))
    data = response.json()
    assert "not implemented" in data["summary"].lower()


# ── Middleware and errors ─────────────────────────────────────────────────────


def test_request_id_generated_when_absent(client):
    response = client.get("/health")
    assert response.headers.get("x-request-id")


def test_request_id_propagated_when_provided(client):
    custom_id = "test-request-id-123"
    response = client.get("/health", headers={"X-Request-Id": custom_id})
    assert response.headers["x-request-id"] == custom_id


def test_internal_error_does_not_expose_internals(client, api_key, monkeypatch):
    from app.api.routes import analyze as analyze_module

    def _boom(request):
        raise RuntimeError("boom - /etc/secret-path")

    monkeypatch.setattr(analyze_module, "generate_placeholder_response", _boom)

    response = client.post("/analyze", json=_body(), headers=_auth_headers(api_key))

    assert response.status_code == 500
    text = response.text
    assert "Traceback" not in text
    assert "/etc/secret-path" not in text
    assert "boom" not in text
    assert "request_id" in response.json()
