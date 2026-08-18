from tests.conftest import MOCK_CHUNK_ID, MOCK_DOCUMENT_ID


def _auth_headers(api_key: str) -> dict:
    return {"X-Api-Key": api_key}


def test_chat_returns_grounded_answer_with_citations(client, api_key):
    response = client.post("/chat", json={"question": "Explain glycolysis"}, headers=_auth_headers(api_key))
    assert response.status_code == 200

    body = response.json()
    assert body["answer"] == "Mocked chat answer for tests."
    assert body["grounded"] is True
    assert len(body["citations"]) == 1
    assert body["citations"][0]["chunkId"] == MOCK_CHUNK_ID
    assert body["citations"][0]["documentId"] == MOCK_DOCUMENT_ID


def test_chat_with_no_retrieved_evidence_returns_ungrounded_answer(client, api_key, monkeypatch):
    from services import qdrant_service as qdrant_module

    monkeypatch.setattr(qdrant_module.qdrant_service, "hybrid_search", lambda *a, **k: [])

    response = client.post("/chat", json={"question": "Explain glycolysis"}, headers=_auth_headers(api_key))
    assert response.status_code == 200

    body = response.json()
    assert body["grounded"] is False
    assert body["citations"] == []
    assert "knowledge base" in body["answer"].lower()


def test_chat_rejects_empty_question(client, api_key):
    response = client.post("/chat", json={"question": ""}, headers=_auth_headers(api_key))
    assert response.status_code == 422


def test_chat_requires_api_key(client):
    response = client.post("/chat", json={"question": "Explain glycolysis"})
    assert response.status_code == 401


def test_chat_rejects_wrong_api_key(client):
    response = client.post("/chat", json={"question": "Explain glycolysis"}, headers=_auth_headers("wrong-key"))
    assert response.status_code == 401
