from app.core.config import Settings
from app.prompting.builders.rag_prompt_builder import RagPromptBuilder
from app.prompting.factory import build_default_prompt_service
from app.prompting.formatting.context_formatter import ContextFormatter
from app.prompting.models.prompt import PromptRequest, PromptTemplateName
from app.retrieval.models.retrieval import SearchRequest, SearchResponse
from tests.prompting.conftest import FakeRetrievalService, make_patient_context


def _settings(**overrides) -> Settings:
    defaults = {
        "AI_API_KEY": "test-ai-key",
        "OPENAI_API_KEY": "test-openai-key",
        "MAX_PROMPT_TOKENS": 1500,
        "MAX_CONTEXT_TOKENS": 800,
        "RESERVED_RESPONSE_TOKENS": 200,
        "DEFAULT_PROMPT_TEMPLATE": "triage",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def test_factory_wires_rag_prompt_builder_and_context_formatter():
    retrieval = FakeRetrievalService(
        response=SearchResponse(query="q", results=[], result_count=0, elapsed_ms=0.0)
    )
    settings = _settings()

    service = build_default_prompt_service(retrieval_service=retrieval, settings=settings)

    assert isinstance(service._prompt_builder, RagPromptBuilder)
    assert isinstance(service._context_formatter, ContextFormatter)
    assert service._default_template == PromptTemplateName.TRIAGE


def test_factory_uses_configured_token_budgets():
    retrieval = FakeRetrievalService(
        response=SearchResponse(query="q", results=[], result_count=0, elapsed_ms=0.0)
    )
    settings = _settings(MAX_PROMPT_TOKENS=999, MAX_CONTEXT_TOKENS=111, RESERVED_RESPONSE_TOKENS=22)

    service = build_default_prompt_service(retrieval_service=retrieval, settings=settings)

    builder = service._prompt_builder
    assert builder._max_prompt_tokens == 999
    assert builder._max_context_tokens == 111
    assert builder._reserved_response_tokens == 22


def test_factory_built_service_produces_a_prompt_end_to_end():
    retrieval = FakeRetrievalService(
        response=SearchResponse(query="q", results=[], result_count=0, elapsed_ms=0.0)
    )
    settings = _settings(DEFAULT_PROMPT_TEMPLATE="diagnosis")

    service = build_default_prompt_service(retrieval_service=retrieval, settings=settings)
    request = PromptRequest(
        patient=make_patient_context(), search_request=SearchRequest(query="fever")
    )
    response = service.build_prompt(request)

    assert "System Instructions" in response.prompt
    assert response.metadata.template == PromptTemplateName.DIAGNOSIS
