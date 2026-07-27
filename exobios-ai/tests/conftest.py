import os

os.environ.setdefault("AI_API_KEY", "test-api-key")
os.environ.setdefault("ENABLE_API_DOCS", "true")
os.environ.setdefault("APP_ENV", "test")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def api_key() -> str:
    return os.environ["AI_API_KEY"]
