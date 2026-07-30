from app.core.config import Settings
from app.generation.factory import build_default_generation_service
from app.generation.providers.openai_provider import OpenAIProvider
from app.generation.validation.response_validator import ResponseValidator
from tests.generation.conftest import (
    make_clinical_draft,
    make_generation_request,
    make_success_response,
)


def _settings(**overrides) -> Settings:
    defaults = {
        "AI_API_KEY": "test-ai-key",
        "OPENAI_API_KEY": "test-openai-key",
        "LLM_MODEL": "gpt-4.1-mini",
        "LLM_TEMPERATURE": 0.2,
        "LLM_MAX_OUTPUT_TOKENS": 1500,
        "LLM_TIMEOUT_SECONDS": 30.0,
        "LLM_MAX_RETRIES": 2,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def test_factory_wires_openai_provider_and_response_validator(fake_openai_client):
    settings = _settings()

    service = build_default_generation_service(settings=settings, openai_client=fake_openai_client)

    assert isinstance(service._provider, OpenAIProvider)
    assert isinstance(service._validator, ResponseValidator)


def test_factory_propagates_settings_to_the_provider(fake_openai_client):
    settings = _settings(
        LLM_MODEL="gpt-4.1",
        LLM_TEMPERATURE=0.7,
        LLM_MAX_OUTPUT_TOKENS=999,
        LLM_TIMEOUT_SECONDS=12.5,
    )

    service = build_default_generation_service(settings=settings, openai_client=fake_openai_client)

    provider = service._provider
    assert provider._model == "gpt-4.1"
    assert provider._temperature == 0.7
    assert provider._max_output_tokens == 999
    assert provider._timeout_seconds == 12.5


def test_factory_propagates_context_window_setting(fake_openai_client):
    settings = _settings(LLM_CONTEXT_WINDOW=8000)

    service = build_default_generation_service(settings=settings, openai_client=fake_openai_client)

    assert service._context_window_tokens == 8000


def test_factory_context_window_defaults_to_none(fake_openai_client):
    settings = _settings()

    service = build_default_generation_service(settings=settings, openai_client=fake_openai_client)

    assert service._context_window_tokens is None


def test_factory_uses_injected_client_instead_of_building_one(fake_openai_client):
    fake_openai_client.responses.response = make_success_response(make_clinical_draft())
    settings = _settings()

    service = build_default_generation_service(settings=settings, openai_client=fake_openai_client)
    service.generate(make_generation_request())

    assert len(fake_openai_client.responses.calls) == 1


def test_factory_makes_no_network_call_during_construction(fake_openai_client):
    settings = _settings()

    build_default_generation_service(settings=settings, openai_client=fake_openai_client)

    assert fake_openai_client.responses.calls == []
