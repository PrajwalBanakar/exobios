import openai
import pytest

from app.generation.exceptions import (
    EmptyModelResponseError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRefusalError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    StructuredOutputError,
)
from app.generation.models.request import GenerationParameters
from app.generation.providers.openai_provider import OpenAIProvider
from tests.generation.conftest import (
    FakeContent,
    FakeIncompleteDetails,
    FakeMessage,
    FakeUsage,
    make_clinical_draft,
    make_generation_request,
    make_httpx_request,
    make_httpx_response,
    make_prompt_response,
    make_success_response,
)


def test_successful_structured_generation_returns_raw_response(fake_openai_client):
    draft = make_clinical_draft()
    fake_openai_client.responses.response = make_success_response(draft)
    provider = OpenAIProvider(client=fake_openai_client)

    raw = provider.generate_structured(make_generation_request())

    assert raw.draft == draft
    assert raw.model == "gpt-4.1-mini"
    assert raw.finish_reason == "completed"
    assert raw.provider_request_id == "req_abc123"


def test_prompt_text_is_forwarded_as_input(fake_openai_client):
    draft = make_clinical_draft()
    fake_openai_client.responses.response = make_success_response(draft)
    provider = OpenAIProvider(client=fake_openai_client)
    request = make_generation_request()

    provider.generate_structured(request)

    call = fake_openai_client.responses.calls[0]
    assert call["input"] == request.prompt_response.prompt
    assert call["text_format"] is not None


def test_default_model_is_used_when_request_has_no_override(fake_openai_client):
    fake_openai_client.responses.response = make_success_response(make_clinical_draft())
    provider = OpenAIProvider(client=fake_openai_client, model="gpt-4.1-mini")

    provider.generate_structured(make_generation_request())

    assert fake_openai_client.responses.calls[0]["model"] == "gpt-4.1-mini"


def test_request_model_override_takes_precedence(fake_openai_client):
    fake_openai_client.responses.response = make_success_response(make_clinical_draft())
    provider = OpenAIProvider(client=fake_openai_client, model="gpt-4.1-mini")

    provider.generate_structured(make_generation_request(model="gpt-4.1"))

    assert fake_openai_client.responses.calls[0]["model"] == "gpt-4.1"


def test_generation_parameters_override_provider_defaults(fake_openai_client):
    fake_openai_client.responses.response = make_success_response(make_clinical_draft())
    provider = OpenAIProvider(
        client=fake_openai_client, temperature=0.2, max_output_tokens=1500, timeout_seconds=30.0
    )
    request = make_generation_request(
        parameters=GenerationParameters(temperature=0.9, max_output_tokens=300, timeout_seconds=5.0)
    )

    provider.generate_structured(request)

    call = fake_openai_client.responses.calls[0]
    assert call["temperature"] == 0.9
    assert call["max_output_tokens"] == 300
    assert call["timeout"] == 5.0


def test_provider_defaults_used_when_parameters_omitted(fake_openai_client):
    fake_openai_client.responses.response = make_success_response(make_clinical_draft())
    provider = OpenAIProvider(
        client=fake_openai_client, temperature=0.3, max_output_tokens=800, timeout_seconds=15.0
    )

    provider.generate_structured(make_generation_request())

    call = fake_openai_client.responses.calls[0]
    assert call["temperature"] == 0.3
    assert call["max_output_tokens"] == 800
    assert call["timeout"] == 15.0


def test_token_usage_is_mapped(fake_openai_client):
    fake_openai_client.responses.response = make_success_response(
        make_clinical_draft(), usage=FakeUsage(input_tokens=321, output_tokens=45, total_tokens=366)
    )
    provider = OpenAIProvider(client=fake_openai_client)

    raw = provider.generate_structured(make_generation_request())

    assert raw.usage.input_tokens == 321
    assert raw.usage.output_tokens == 45
    assert raw.usage.total_tokens == 366


def test_missing_usage_defaults_to_zero(fake_openai_client):
    response = make_success_response(make_clinical_draft())
    response.usage = None
    fake_openai_client.responses.response = response
    provider = OpenAIProvider(client=fake_openai_client)

    raw = provider.generate_structured(make_generation_request())

    assert raw.usage.input_tokens == 0
    assert raw.usage.output_tokens == 0
    assert raw.usage.total_tokens == 0


def test_finish_reason_maps_completed_status(fake_openai_client):
    fake_openai_client.responses.response = make_success_response(
        make_clinical_draft(), status="completed"
    )
    provider = OpenAIProvider(client=fake_openai_client)

    raw = provider.generate_structured(make_generation_request())

    assert raw.finish_reason == "completed"


def test_finish_reason_maps_incomplete_status_with_reason(fake_openai_client):
    draft = make_clinical_draft()
    fake_openai_client.responses.response = make_success_response(
        draft,
        status="incomplete",
        incomplete_details=FakeIncompleteDetails(reason="max_output_tokens"),
    )
    provider = OpenAIProvider(client=fake_openai_client)

    raw = provider.generate_structured(make_generation_request())

    assert raw.finish_reason == "incomplete:max_output_tokens"


def test_provider_request_id_is_captured_when_present(fake_openai_client):
    fake_openai_client.responses.response = make_success_response(
        make_clinical_draft(), request_id="req_xyz789"
    )
    provider = OpenAIProvider(client=fake_openai_client)

    raw = provider.generate_structured(make_generation_request())

    assert raw.provider_request_id == "req_xyz789"


def test_provider_request_id_is_none_when_absent(fake_openai_client):
    fake_openai_client.responses.response = make_success_response(
        make_clinical_draft(), request_id=None
    )
    provider = OpenAIProvider(client=fake_openai_client)

    raw = provider.generate_structured(make_generation_request())

    assert raw.provider_request_id is None


def test_empty_output_raises_empty_model_response_error(fake_openai_client):
    fake_openai_client.responses.response = make_success_response(
        make_clinical_draft(), output=[], output_parsed=None
    )
    provider = OpenAIProvider(client=fake_openai_client)

    with pytest.raises(EmptyModelResponseError):
        provider.generate_structured(make_generation_request())


def test_refusal_raises_provider_refusal_error(fake_openai_client):
    fake_openai_client.responses.response = make_success_response(
        make_clinical_draft(),
        output=[
            FakeMessage([FakeContent(type="refusal", refusal="Cannot assist with this request.")])
        ],
        output_parsed=None,
    )
    provider = OpenAIProvider(client=fake_openai_client)

    with pytest.raises(ProviderRefusalError) as exc_info:
        provider.generate_structured(make_generation_request())

    assert "Cannot assist" in exc_info.value.reason


def test_malformed_output_raises_structured_output_error(fake_openai_client):
    fake_openai_client.responses.response = make_success_response(
        make_clinical_draft(),
        output=[FakeMessage([FakeContent(type="output_text", parsed=None)])],
        output_parsed=None,
        status="incomplete",
    )
    provider = OpenAIProvider(client=fake_openai_client)

    with pytest.raises(StructuredOutputError):
        provider.generate_structured(make_generation_request())


def test_authentication_error_is_mapped(fake_openai_client):
    fake_openai_client.responses.fail_with = openai.AuthenticationError(
        "invalid api key", response=make_httpx_response(401), body=None
    )
    provider = OpenAIProvider(client=fake_openai_client)

    with pytest.raises(ProviderAuthenticationError):
        provider.generate_structured(make_generation_request())


def test_rate_limit_error_is_mapped(fake_openai_client):
    fake_openai_client.responses.fail_with = openai.RateLimitError(
        "rate limited", response=make_httpx_response(429), body=None
    )
    provider = OpenAIProvider(client=fake_openai_client)

    with pytest.raises(ProviderRateLimitError):
        provider.generate_structured(make_generation_request())


def test_timeout_error_is_mapped(fake_openai_client):
    fake_openai_client.responses.fail_with = openai.APITimeoutError(request=make_httpx_request())
    provider = OpenAIProvider(client=fake_openai_client)

    with pytest.raises(ProviderTimeoutError):
        provider.generate_structured(make_generation_request())


def test_generic_api_error_is_mapped_to_provider_unavailable(fake_openai_client):
    fake_openai_client.responses.fail_with = openai.InternalServerError(
        "server error", response=make_httpx_response(500), body=None
    )
    provider = OpenAIProvider(client=fake_openai_client)

    with pytest.raises(ProviderUnavailableError):
        provider.generate_structured(make_generation_request())


def test_unexpected_exception_is_wrapped_as_provider_unavailable(fake_openai_client):
    fake_openai_client.responses.fail_with = RuntimeError("something broke")
    provider = OpenAIProvider(client=fake_openai_client)

    with pytest.raises(ProviderUnavailableError):
        provider.generate_structured(make_generation_request())


def test_health_returns_true_for_a_configured_client(fake_openai_client):
    provider = OpenAIProvider(client=fake_openai_client)

    assert provider.health() is True


def test_health_does_not_call_the_client(fake_openai_client):
    provider = OpenAIProvider(client=fake_openai_client)

    provider.health()

    assert fake_openai_client.responses.calls == []


def test_no_sensitive_prompt_content_in_logs(fake_openai_client, caplog):
    draft = make_clinical_draft()
    fake_openai_client.responses.response = make_success_response(draft)
    provider = OpenAIProvider(client=fake_openai_client)
    request = make_generation_request(
        prompt_response=make_prompt_response(prompt="SENSITIVE PATIENT COMPLAINT TEXT")
    )

    with caplog.at_level("DEBUG"):
        provider.generate_structured(request)

    for record in caplog.records:
        assert "SENSITIVE PATIENT COMPLAINT TEXT" not in record.getMessage()
