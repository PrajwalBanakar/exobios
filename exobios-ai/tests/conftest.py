import os

# Required settings with no defaults (see app/config/settings.py) must be set
# before `app.main` is imported anywhere below, since `Settings()` is
# constructed at module import time and raises if any are missing.
os.environ.setdefault("AI_API_KEY", "test-api-key")
os.environ.setdefault("QDRANT__URL", "http://localhost:6333")
os.environ.setdefault("EMBEDDING__HF_TOKEN", "test-hf-token")
os.environ.setdefault("RERANKER__HF_TOKEN", "test-hf-token")
os.environ.setdefault("LLM__GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("MONGO__URI", "mongodb://localhost:27017")
# Disabled by default so the ~60 /analyze calls the rest of this suite makes
# don't trip the limiter and make unrelated tests flaky. test_rate_limit.py
# re-enables it explicitly (and swaps in its own small RateLimiter instance)
# for the tests that actually exercise this behavior.
os.environ.setdefault("RATE_LIMIT__ENABLED", "false")

import pytest
from fastapi.testclient import TestClient

# Deliberately unqualified imports (`main`, `schemas...`), NOT `app.main` /
# `app.schemas...`: app/main.py and everything it imports use unqualified
# imports internally (`from api.routes import ...`, etc.), which resolve via
# app/ being on sys.path (see pytest.ini's `pythonpath = app`). Importing the
# same modules here as `app.xxx` would load them a SECOND time under a
# different sys.modules key — a different module object with different
# classes, so e.g. a `SupportingCitation` built from `app.schemas...` would
# fail pydantic validation against the app-internal `SupportingCitation`
# class, and monkeypatching `app.services.x` would patch an instance nothing
# else ever calls. Keep every internal import in this test suite unqualified.
from main import app
from schemas.stages.common import SupportingCitation
from schemas.stages.deterministic_rule import Severity
from schemas.stages.diagnosis import DiagnosisCandidate, DiagnosisResult
from schemas.stages.investigation import InvestigationResult, RecommendedTest, UrgencyLevel
from schemas.stages.plan_of_action import ImmediateMeasure, PlanOfActionResult
from schemas.stages.treatment_protocol import TreatmentProtocolResult, TreatmentStep

# ── Fixed identifiers shared between the mocked Qdrant results and the mocked
# LLM output, so a citation the fake LLM returns always matches a chunk that
# was actually "retrieved" — otherwise every test would trip the citation
# verification added in app/graph/nodes/validation.py. Tests that want to
# exercise verification failure/insufficient-evidence paths override the
# relevant fixture explicitly (see test_analyze.py).
MOCK_CHUNK_ID = "11111111-1111-1111-1111-111111111111"
MOCK_DOCUMENT_ID = "22222222-2222-2222-2222-222222222222"
MOCK_EXCERPT = "Mocked clinical excerpt used only in tests."


def mock_qdrant_candidate(chunk_id: str = MOCK_CHUNK_ID) -> dict:
    return {
        "chunk_id": chunk_id,
        "text": MOCK_EXCERPT,
        "payload": {
            "document_payload": {"document_id": MOCK_DOCUMENT_ID},
            "chunk_payload": {"chunk_metadata": {"content": MOCK_EXCERPT, "heading": "Mock Heading", "page_start": 1}},
        },
        "score": 0.9,
    }


def mock_citation(chunk_id: str = MOCK_CHUNK_ID) -> SupportingCitation:
    return SupportingCitation(chunk_id=chunk_id, document_id=MOCK_DOCUMENT_ID, excerpt=MOCK_EXCERPT, heading="Mock Heading", page=1)


def fake_generate_structured(system_prompt, user_prompt, response_schema):
    """Deterministic stand-in for llm_service.generate_structured — returns a
    minimal, schema-valid, self-consistent object per stage so the full graph
    can run end-to-end offline. Always cites MOCK_CHUNK_ID so it matches
    whatever mock_qdrant_candidate() produced for that request."""
    citation = mock_citation()
    if response_schema is DiagnosisResult:
        return DiagnosisResult(
            candidates=[DiagnosisCandidate(
                disease_name="Mock Diagnosis", confidence_score=0.6, confidence_label="MEDIUM",
                citations=[citation], reasoning="Mocked reasoning for tests.",
            )],
            query_used="mock query",
        )
    if response_schema is InvestigationResult:
        return InvestigationResult(
            tests=[RecommendedTest(test_name="Mock Test", urgency=UrgencyLevel.MEDIUM, rationale="Mocked.", citations=[citation])],
            based_on_diagnosis=["Mock Diagnosis"],
        )
    if response_schema is TreatmentProtocolResult:
        return TreatmentProtocolResult(
            steps=[TreatmentStep(order=1, instruction="Mocked treatment step.", citations=[citation])],
            based_on_diagnosis=["Mock Diagnosis"],
        )
    if response_schema is PlanOfActionResult:
        return PlanOfActionResult(
            immediate_measures=[ImmediateMeasure(order=1, action="Mocked measure.")],
            warning_signs=[],
            risk_level=Severity.LOW,
            referral_advice=None,
        )
    raise AssertionError(f"fake_generate_structured got an unexpected schema: {response_schema}")


@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch):
    """Every test runs fully offline by default — no real Qdrant, HF,
    Groq, or Mongo calls. Individual tests can further monkeypatch these
    same targets to simulate specific failures."""
    from services import embedding_service as embedding_module
    from services import llm_service as llm_module
    from services import qdrant_service as qdrant_module
    from services import reranker_service as reranker_module
    from repositories import assesment as assesment_module

    monkeypatch.setattr(embedding_module.embedding_service, "embed", lambda text: [0.0] * 384)
    monkeypatch.setattr(qdrant_module.qdrant_service, "hybrid_search", lambda *a, **k: [mock_qdrant_candidate()])
    monkeypatch.setattr(reranker_module.reranker_service, "rerank", lambda query, candidates, top_k: candidates[:top_k])
    monkeypatch.setattr(llm_module.llm_service, "generate_structured", fake_generate_structured)
    monkeypatch.setattr(assesment_module, "upsert_assessment", lambda assessment_id, data: None)
    monkeypatch.setattr(assesment_module, "get_assessment", lambda assessment_id: None)
    monkeypatch.setattr(assesment_module, "ping", lambda: None)

    class _FakeQdrantClient:
        def get_collections(self):
            return object()

        def retrieve(self, collection_name, ids, with_payload=True):
            return []  # simulates a corpus with no compatibility metadata yet — non-fatal

    monkeypatch.setattr(qdrant_module.qdrant_service, "client", _FakeQdrantClient())
    # hybrid_search is mocked above and never calls verify_embedding_compatibility
    # itself, but /health/ready calls it directly — pre-mark it checked with no
    # warning so readiness tests default to a clean "ok" unless a test overrides this.
    monkeypatch.setattr(qdrant_module.qdrant_service, "_compatibility_checked", True)
    monkeypatch.setattr(qdrant_module.qdrant_service, "compatibility_warning", None)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def api_key() -> str:
    return os.environ["AI_API_KEY"]
