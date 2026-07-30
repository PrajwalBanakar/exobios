from pathlib import Path
from uuid import uuid4

import pytest
from jinja2 import Environment, FileSystemLoader

from app.prompting.models.prompt import PatientContext
from app.retrieval.models.retrieval import SearchResponse
from app.schemas.analyze import ComplaintCategory, SymptomSummary, VitalsSummary

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "prompting" / "templates"


class FakeRetrievalService:
    """Stands in for RetrievalService: PromptService only calls .search(),
    so a duck-typed fake avoids needing a real EmbeddingProvider/Retriever/
    Reranker stack for PromptService-level unit tests."""

    def __init__(
        self, response: SearchResponse | None = None, fail_with: Exception | None = None
    ) -> None:
        self.response = response
        self.fail_with = fail_with
        self.calls: list = []

    def search(self, request) -> SearchResponse:
        if self.fail_with is not None:
            raise self.fail_with
        self.calls.append(request)
        return self.response if self.response is not None else SearchResponse(
            query=request.query, results=[], result_count=0, elapsed_ms=0.0
        )


class FakePromptBuilder:
    def __init__(self, response=None, fail_with: Exception | None = None) -> None:
        self.response = response
        self.fail_with = fail_with
        self.calls: list = []

    def build(self, context, template):
        if self.fail_with is not None:
            raise self.fail_with
        self.calls.append((context, template))
        return self.response


class FakeContextFormatter:
    def __init__(self, response=None, fail_with: Exception | None = None) -> None:
        self.response = response
        self.fail_with = fail_with
        self.calls: list = []

    def format(self, chunks):
        if self.fail_with is not None:
            raise self.fail_with
        self.calls.append(chunks)
        return self.response


@pytest.fixture
def jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def make_patient_context(**overrides) -> PatientContext:
    defaults = {
        "assessment_id": uuid4(),
        "patient_id": uuid4(),
        "patient_complaint": "fever and cough",
        "complaint_category": ComplaintCategory.FEVER,
        "symptoms": [SymptomSummary(name="fever", duration="2 days", severity="moderate")],
        "vitals": VitalsSummary(heart_rate=90, spo2=97.0, temperature=38.5),
        "past_illnesses": None,
        "current_medications": None,
        "allergies": None,
    }
    defaults.update(overrides)
    return PatientContext(**defaults)
