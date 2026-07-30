from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest

from app.generation.models.request import GenerationRequest
from app.generation.models.response import (
    ClinicalGenerationDraft,
    ClinicalGenerationOutput,
    PossibleCondition,
    RawGenerationResponse,
    RecommendedAction,
    RiskAssessment,
)
from app.generation.models.usage import TokenUsage
from app.ingestion.models.document import DocumentType
from app.prompting.models.prompt import (
    CitedChunk,
    DocumentGroup,
    PromptMetadata,
    PromptResponse,
    PromptStatistics,
    PromptTemplateName,
    RetrievedContext,
)
from app.retrieval.models.retrieval import RetrievedChunk


def make_httpx_request() -> httpx.Request:
    return httpx.Request("POST", "https://api.openai.com/v1/responses")


def make_httpx_response(status_code: int) -> httpx.Response:
    return httpx.Response(status_code=status_code, request=make_httpx_request())


def make_retrieved_chunk_for_generation(**overrides) -> RetrievedChunk:
    defaults = {
        "document_id": uuid4(),
        "chunk_id": uuid4(),
        "score": 0.9,
        "text": "Fever is a common presenting symptom.",
        "page_number": 1,
        "section_title": None,
        "document_type": DocumentType.PDF,
        "filename": "guide.pdf",
        "language": "en",
        "tags": [],
        "version": "1.0",
        "source": "textbook",
    }
    defaults.update(overrides)
    return RetrievedChunk(**defaults)


def make_retrieved_context(
    citation_numbers: tuple[int, ...] = (1,), **chunk_overrides
) -> RetrievedContext:
    chunk = make_retrieved_chunk_for_generation(**chunk_overrides)
    cited = [CitedChunk(citation_number=n, chunk=chunk) for n in citation_numbers]
    group = DocumentGroup(
        document_id=chunk.document_id,
        filename=chunk.filename,
        document_type=chunk.document_type,
        source=chunk.source,
        citations=cited,
    )
    return RetrievedContext(groups=[group], total_chunks=len(cited))


def make_prompt_response(
    retrieved_context: RetrievedContext | None = None, prompt: str = "a prompt", **stat_overrides
) -> PromptResponse:
    if retrieved_context is None:
        retrieved_context = make_retrieved_context()
    stats_defaults = {
        "prompt_tokens": 10,
        "context_tokens": 5,
        "reserved_response_tokens": 500,
        "max_prompt_tokens": 4000,
        "retrieved_chunk_count": retrieved_context.total_chunks,
        "included_chunk_count": retrieved_context.total_chunks,
        "discarded_chunk_count": 0,
    }
    stats_defaults.update(stat_overrides)
    return PromptResponse(
        prompt=prompt,
        sections=[],
        metadata=PromptMetadata(
            assessment_id=uuid4(),
            template=PromptTemplateName.DIAGNOSIS,
            created_at=datetime.now(UTC),
            section_names=[],
            citation_count=retrieved_context.total_chunks,
        ),
        statistics=PromptStatistics(**stats_defaults),
        retrieved_context=retrieved_context,
    )


def make_clinical_draft(
    citation_numbers: tuple[int, ...] = (1,), **overrides
) -> ClinicalGenerationDraft:
    numbers = list(citation_numbers)
    defaults = {
        "summary": "Patient presents with fever and mild fatigue.",
        "possible_conditions": [
            PossibleCondition(
                name="Viral infection",
                likelihood="MODERATE",
                reasoning="Fever without focal findings",
                supporting_citation_numbers=numbers,
            )
        ],
        "risk_assessment": RiskAssessment(
            level="LOW",
            reasoning="No red flags identified",
            requires_immediate_escalation=False,
            supporting_citation_numbers=numbers,
        ),
        "red_flags": [],
        "recommended_actions": [
            RecommendedAction(
                action="Monitor temperature and hydration",
                priority="ROUTINE",
                reasoning="Standard supportive care",
                supporting_citation_numbers=numbers,
            )
        ],
        "follow_up_questions": ["How long has the fever persisted?"],
        "citations": numbers,
        "limitations": ["Limited history available"],
    }
    defaults.update(overrides)
    return ClinicalGenerationDraft(**defaults)


def make_generation_request(**overrides) -> GenerationRequest:
    defaults = {"prompt_response": make_prompt_response()}
    defaults.update(overrides)
    return GenerationRequest(**defaults)


def make_clinical_output(
    citation_numbers: tuple[int, ...] = (1,), **overrides
) -> ClinicalGenerationOutput:
    draft = make_clinical_draft(citation_numbers=citation_numbers).model_dump(exclude={"citations"})
    citations = [
        {
            "citation_number": n,
            "document_id": uuid4(),
            "chunk_id": uuid4(),
            "filename": "guide.pdf",
            "page_number": 1,
            "source": "textbook",
        }
        for n in citation_numbers
    ]
    defaults = {**draft, "citations": citations}
    defaults.update(overrides)
    return ClinicalGenerationOutput(**defaults)


def make_raw_generation_response(**overrides) -> RawGenerationResponse:
    defaults = {
        "draft": make_clinical_draft(),
        "model": "gpt-4.1-mini",
        "usage": TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
        "finish_reason": "completed",
        "provider_request_id": "req_abc123",
        "latency_ms": 42.0,
    }
    defaults.update(overrides)
    return RawGenerationResponse(**defaults)


class FakeContent:
    def __init__(self, type: str = "output_text", parsed=None, refusal: str | None = None) -> None:
        self.type = type
        self.parsed = parsed
        self.refusal = refusal


class FakeMessage:
    def __init__(self, content: list[FakeContent]) -> None:
        self.type = "message"
        self.content = content


class FakeIncompleteDetails:
    def __init__(self, reason: str) -> None:
        self.reason = reason


class FakeUsage:
    def __init__(
        self, input_tokens: int = 100, output_tokens: int = 50, total_tokens: int = 150
    ) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = total_tokens


class FakeParsedResponse:
    """Stands in for openai.types.responses.ParsedResponse: only the
    attributes OpenAIProvider actually reads."""

    def __init__(
        self,
        output=None,
        output_parsed=None,
        status: str = "completed",
        incomplete_details: FakeIncompleteDetails | None = None,
        usage: FakeUsage | None = None,
        model: str = "gpt-4.1-mini",
        request_id: str | None = "req_abc123",
    ) -> None:
        self.output = output if output is not None else []
        self.output_parsed = output_parsed
        self.status = status
        self.incomplete_details = incomplete_details
        self.usage = usage if usage is not None else FakeUsage()
        self.model = model
        if request_id is not None:
            self._request_id = request_id


def make_success_response(draft: ClinicalGenerationDraft, **overrides) -> FakeParsedResponse:
    defaults = {
        "output": [FakeMessage([FakeContent(type="output_text", parsed=draft)])],
        "output_parsed": draft,
    }
    defaults.update(overrides)
    return FakeParsedResponse(**defaults)


class FakeResponsesAPI:
    def __init__(self, response=None, fail_with: Exception | None = None) -> None:
        self.response = response
        self.fail_with = fail_with
        self.calls: list[dict] = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_with is not None:
            raise self.fail_with
        return self.response


class FakeOpenAIClient:
    """Stands in for `openai.OpenAI`: only implements
    `.responses.parse(...)`, mirroring the shape OpenAIProvider actually
    calls, with no network access."""

    def __init__(self, response=None, fail_with: Exception | None = None) -> None:
        self.responses = FakeResponsesAPI(response=response, fail_with=fail_with)


@pytest.fixture
def fake_openai_client() -> FakeOpenAIClient:
    return FakeOpenAIClient()


class FakeLLMProvider:
    """Stands in for LLMProvider, recording calls without a real client."""

    def __init__(self, response=None, fail_with: Exception | None = None) -> None:
        self.response = response
        self.fail_with = fail_with
        self.calls: list = []
        self.health_result = True

    def generate_structured(self, request):
        self.calls.append(request)
        if self.fail_with is not None:
            raise self.fail_with
        return self.response

    def health(self) -> bool:
        return self.health_result


class FakeResponseValidator:
    """Stands in for ResponseValidator, recording calls without running
    real deterministic checks."""

    def __init__(self, response=None, fail_with: Exception | None = None) -> None:
        self.response = response
        self.fail_with = fail_with
        self.calls: list = []

    def validate_and_resolve(self, draft, retrieved_context):
        self.calls.append((draft, retrieved_context))
        if self.fail_with is not None:
            raise self.fail_with
        return self.response
