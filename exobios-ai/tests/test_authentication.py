import uuid


def _valid_body() -> dict:
    return {
        "assessmentId": str(uuid.uuid4()),
        "patientId": str(uuid.uuid4()),
        "symptoms": [],
    }


def test_analyze_rejects_missing_api_key(client):
    response = client.post("/analyze", json=_valid_body())
    assert response.status_code == 401


def test_analyze_rejects_incorrect_api_key(client):
    response = client.post("/analyze", json=_valid_body(), headers={"X-Api-Key": "wrong-key"})
    assert response.status_code == 401


def test_analyze_accepts_configured_api_key(client, api_key):
    response = client.post("/analyze", json=_valid_body(), headers={"X-Api-Key": api_key})
    assert response.status_code == 200


def test_api_key_never_present_in_response_body(client, api_key):
    response = client.post("/analyze", json=_valid_body(), headers={"X-Api-Key": api_key})
    assert api_key not in response.text


def test_api_key_never_present_in_error_response(client):
    response = client.post("/analyze", json=_valid_body())
    assert "test-api-key" not in response.text
