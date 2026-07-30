import pytest

from app.generation.exceptions import (
    GenerationValidationError,
    PromptBudgetExceededError,
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from app.generation.services.generation_service import GenerationService
from tests.generation.conftest import (
    FakeLLMProvider,
    FakeResponseValidator,
    make_clinical_output,
    make_generation_request,
    make_prompt_response,
    make_raw_generation_response,
)


def test_successful_generation_returns_provider_independent_result():
    raw = make_raw_generation_response()
    output = make_clinical_output()
    provider = FakeLLMProvider(response=raw)
    validator = FakeResponseValidator(response=output)
    service = GenerationService(provider=provider, validator=validator)
    request = make_generation_request()

    result = service.generate(request)

    assert result.request_id == request.request_id
    assert result.output is output
    assert result.resolved_citations == output.citations
    assert result.metadata.model == raw.model
    assert result.metadata.usage == raw.usage
    assert result.metadata.finish_reason == raw.finish_reason
    assert result.metadata.provider_request_id == raw.provider_request_id
    assert len(provider.calls) == 1
    assert validator.calls[0][0] == raw.draft
    assert validator.calls[0][1] is request.prompt_response.retrieved_context


def test_blank_prompt_is_rejected_before_calling_provider():
    provider = FakeLLMProvider()
    validator = FakeResponseValidator()
    service = GenerationService(provider=provider, validator=validator)
    request = make_generation_request(prompt_response=make_prompt_response(prompt="   "))

    with pytest.raises(GenerationValidationError, match="blank"):
        service.generate(request)

    assert provider.calls == []


def test_prompt_budget_exceeded_is_rejected_before_calling_provider():
    provider = FakeLLMProvider()
    validator = FakeResponseValidator()
    service = GenerationService(provider=provider, validator=validator, context_window_tokens=100)
    request = make_generation_request(
        prompt_response=make_prompt_response(prompt_tokens=90, reserved_response_tokens=50)
    )

    with pytest.raises(PromptBudgetExceededError):
        service.generate(request)

    assert provider.calls == []


def test_prompt_budget_check_is_skipped_when_context_window_not_configured():
    raw = make_raw_generation_response()
    output = make_clinical_output()
    provider = FakeLLMProvider(response=raw)
    validator = FakeResponseValidator(response=output)
    service = GenerationService(provider=provider, validator=validator, context_window_tokens=None)
    request = make_generation_request(
        prompt_response=make_prompt_response(
            prompt_tokens=1_000_000, reserved_response_tokens=1_000_000
        )
    )

    result = service.generate(request)

    assert result.output is output


def test_prompt_within_budget_is_accepted():
    raw = make_raw_generation_response()
    output = make_clinical_output()
    provider = FakeLLMProvider(response=raw)
    validator = FakeResponseValidator(response=output)
    service = GenerationService(provider=provider, validator=validator, context_window_tokens=1000)
    request = make_generation_request(
        prompt_response=make_prompt_response(prompt_tokens=100, reserved_response_tokens=100)
    )

    result = service.generate(request)

    assert result.output is output


def test_provider_exception_propagates_unwrapped():
    provider = FakeLLMProvider(fail_with=ProviderRateLimitError(reason="slow down"))
    validator = FakeResponseValidator()
    service = GenerationService(provider=provider, validator=validator)

    with pytest.raises(ProviderRateLimitError):
        service.generate(make_generation_request())


def test_unexpected_provider_exception_is_wrapped():
    provider = FakeLLMProvider(fail_with=RuntimeError("boom"))
    validator = FakeResponseValidator()
    service = GenerationService(provider=provider, validator=validator)

    with pytest.raises(ProviderUnavailableError):
        service.generate(make_generation_request())


def test_validation_exception_propagates_unwrapped():
    raw = make_raw_generation_response()
    provider = FakeLLMProvider(response=raw)
    validator = FakeResponseValidator(fail_with=GenerationValidationError(reason="bad citation"))
    service = GenerationService(provider=provider, validator=validator)

    with pytest.raises(GenerationValidationError):
        service.generate(make_generation_request())


def test_unexpected_validation_exception_is_wrapped():
    raw = make_raw_generation_response()
    provider = FakeLLMProvider(response=raw)
    validator = FakeResponseValidator(fail_with=RuntimeError("boom"))
    service = GenerationService(provider=provider, validator=validator)

    with pytest.raises(GenerationValidationError):
        service.generate(make_generation_request())


def test_metadata_preserves_token_usage_and_latency():
    raw = make_raw_generation_response(latency_ms=987.6)
    output = make_clinical_output()
    provider = FakeLLMProvider(response=raw)
    validator = FakeResponseValidator(response=output)
    service = GenerationService(provider=provider, validator=validator)

    result = service.generate(make_generation_request())

    assert result.metadata.latency_ms == 987.6
    assert result.metadata.usage.total_tokens == raw.usage.total_tokens


def test_logs_each_pipeline_stage(caplog):
    raw = make_raw_generation_response()
    output = make_clinical_output()
    provider = FakeLLMProvider(response=raw)
    validator = FakeResponseValidator(response=output)
    service = GenerationService(provider=provider, validator=validator)

    with caplog.at_level("INFO", logger="app.generation"):
        service.generate(make_generation_request())

    messages = " ".join(record.message for record in caplog.records)
    for expected in (
        "generation_started",
        "provider_request_started",
        "provider_request_completed",
        "generation_validation_started",
        "generation_validation_completed",
        "generation_completed",
    ):
        assert expected in messages


def test_logs_generation_failed_on_provider_error(caplog):
    provider = FakeLLMProvider(fail_with=RuntimeError("boom"))
    validator = FakeResponseValidator()
    service = GenerationService(provider=provider, validator=validator)

    with caplog.at_level("ERROR", logger="app.generation"), pytest.raises(ProviderUnavailableError):
        service.generate(make_generation_request())

    messages = " ".join(record.message for record in caplog.records)
    assert "provider_request_failed" in messages
    assert "generation_failed" in messages


def test_logs_generation_failed_on_validation_error(caplog):
    raw = make_raw_generation_response()
    provider = FakeLLMProvider(response=raw)
    validator = FakeResponseValidator(fail_with=GenerationValidationError(reason="bad citation"))
    service = GenerationService(provider=provider, validator=validator)

    with (
        caplog.at_level("ERROR", logger="app.generation"),
        pytest.raises(GenerationValidationError),
    ):
        service.generate(make_generation_request())

    messages = " ".join(record.message for record in caplog.records)
    assert "generation_validation_failed" in messages
    assert "generation_failed" in messages


def test_no_sensitive_content_in_logs(caplog):
    raw = make_raw_generation_response()
    output = make_clinical_output()
    provider = FakeLLMProvider(response=raw)
    validator = FakeResponseValidator(response=output)
    service = GenerationService(provider=provider, validator=validator)
    request = make_generation_request(
        prompt_response=make_prompt_response(prompt="SENSITIVE PATIENT COMPLAINT TEXT")
    )

    with caplog.at_level("DEBUG"):
        service.generate(request)

    for record in caplog.records:
        assert "SENSITIVE PATIENT COMPLAINT TEXT" not in record.getMessage()
