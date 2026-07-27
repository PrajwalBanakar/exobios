def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_matches_schema(client):
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "UP"
    assert body["service"] == "exobios-ai"
    assert isinstance(body["version"], str)


def test_health_does_not_require_api_key(client):
    response = client.get("/health")
    assert response.status_code == 200
