import os

os.environ.setdefault("AI_API_KEY", "test-api-key")
os.environ.setdefault("ENABLE_API_DOCS", "true")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
# Tests assume OpenAI-only wiring by default. Without this, a real
# GEMINI_API_KEY in a developer's local .env (e.g. for the Gemini demo
# pipeline) would leak into every test's Settings() and silently flip
# the embeddings/generation/retrieval factories over to Gemini.
os.environ.setdefault("GEMINI_API_KEY", "")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def api_key() -> str:
    return os.environ["AI_API_KEY"]
