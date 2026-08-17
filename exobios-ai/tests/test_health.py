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


def test_readiness_up_when_dependencies_reachable(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "UP"
    assert body["checks"]["mongo"] == "ok"
    assert body["checks"]["qdrant"] == "ok"


def test_readiness_down_when_mongo_unreachable(client, monkeypatch):
    from repositories import assesment as assesment_module

    def _boom():
        raise ConnectionError("mongo unreachable")

    monkeypatch.setattr(assesment_module, "ping", _boom)

    response = client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "DOWN"
    assert "unreachable" in body["checks"]["mongo"]
    assert body["checks"]["qdrant"] == "ok"


def test_readiness_down_when_qdrant_unreachable(client, monkeypatch):
    from services import qdrant_service as qdrant_module

    class _BoomClient:
        def get_collections(self):
            raise ConnectionError("qdrant unreachable")

    monkeypatch.setattr(qdrant_module.qdrant_service, "client", _BoomClient())

    response = client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "DOWN"
    assert "unreachable" in body["checks"]["qdrant"]


def test_readiness_does_not_require_api_key(client):
    response = client.get("/health/ready")
    assert response.status_code in (200, 503)
