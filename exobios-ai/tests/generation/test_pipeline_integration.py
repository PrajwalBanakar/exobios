import pytest

from app.generation.exceptions import (
    EmptyModelResponseError,
    GenerationValidationError,
    ProviderRefusalError,
    StructuredOutputError,
)
from app.generation.models.response import RiskAssessment
from app.generation.providers.openai_provider import OpenAIProvider
from app.generation.services.generation_service import GenerationService
from app.generation.validation.response_validator import ResponseValidator
from tests.generation.conftest import (
    FakeContent,
    FakeMessage,
    FakeOpenAIClient,
    make_clinical_draft,
    make_generation_request,
    make_prompt_response,
    make_retrieved_context,
    make_success_response,
)


def _build_service(fake_client) -> GenerationService:
    provider = OpenAIProvider(client=fake_client)
    validator = ResponseValidator()
    return GenerationService(provider=provider, validator=validator)


def test_prompt_response_flows_to_validated_generation_result():
    retrieved_context = make_retrieved_context(citation_numbers=(1,))
    chunk = retrieved_context.groups[0].citations[0].chunk
    draft = make_clinical_draft(citation_numbers=(1,))
    fake_client = FakeOpenAIClient(response=make_success_response(draft))
    service = _build_service(fake_client)
    request = make_generation_request(
        prompt_response=make_prompt_response(retrieved_context=retrieved_context)
    )

    result = service.generate(request)

    assert result.output.summary == draft.summary
    assert len(result.resolved_citations) == 1
    citation = result.resolved_citations[0]
    assert citation.document_id == chunk.document_id
    assert citation.chunk_id == chunk.chunk_id
    assert citation.filename == chunk.filename
    assert citation.source == chunk.source
    assert result.metadata.model == "gpt-4.1-mini"
    assert result.metadata.finish_reason == "completed"


def test_invalid_model_citation_is_rejected_end_to_end():
    retrieved_context = make_retrieved_context(citation_numbers=(1,))
    draft = make_clinical_draft(citation_numbers=(1, 77))  # 77 was never retrieved
    fake_client = FakeOpenAIClient(response=make_success_response(draft))
    service = _build_service(fake_client)
    request = make_generation_request(
        prompt_response=make_prompt_response(retrieved_context=retrieved_context)
    )

    with pytest.raises(GenerationValidationError, match="77"):
        service.generate(request)


def test_critical_escalation_invariant_end_to_end():
    retrieved_context = make_retrieved_context(citation_numbers=(1,))
    draft = make_clinical_draft(
        citation_numbers=(1,),
        risk_assessment=RiskAssessment(
            level="CRITICAL", reasoning="Severe presentation", requires_immediate_escalation=False
        ),
    )
    fake_client = FakeOpenAIClient(response=make_success_response(draft))
    service = _build_service(fake_client)
    request = make_generation_request(
        prompt_response=make_prompt_response(retrieved_context=retrieved_context)
    )

    with pytest.raises(GenerationValidationError, match="CRITICAL"):
        service.generate(request)


def test_provider_refusal_end_to_end():
    fake_client = FakeOpenAIClient(
        response=make_success_response(
            make_clinical_draft(),
            output=[FakeMessage([FakeContent(type="refusal", refusal="Cannot help with this.")])],
            output_parsed=None,
        )
    )
    service = _build_service(fake_client)

    with pytest.raises(ProviderRefusalError):
        service.generate(make_generation_request())


def test_malformed_structured_output_end_to_end():
    fake_client = FakeOpenAIClient(
        response=make_success_response(
            make_clinical_draft(),
            output=[FakeMessage([FakeContent(type="output_text", parsed=None)])],
            output_parsed=None,
            status="incomplete",
        )
    )
    service = _build_service(fake_client)

    with pytest.raises(StructuredOutputError):
        service.generate(make_generation_request())


def test_empty_response_end_to_end():
    fake_client = FakeOpenAIClient(
        response=make_success_response(make_clinical_draft(), output=[], output_parsed=None)
    )
    service = _build_service(fake_client)

    with pytest.raises(EmptyModelResponseError):
        service.generate(make_generation_request())


def test_insufficient_evidence_response_end_to_end():
    retrieved_context = make_retrieved_context(citation_numbers=(1,))
    draft = make_clinical_draft(
        citation_numbers=(1,),
        possible_conditions=[],
        citations=[],
        limitations=["Evidence is insufficient to suggest a specific condition."],
    )
    fake_client = FakeOpenAIClient(response=make_success_response(draft))
    service = _build_service(fake_client)
    request = make_generation_request(
        prompt_response=make_prompt_response(retrieved_context=retrieved_context)
    )

    result = service.generate(request)

    assert result.output.possible_conditions == []
    assert result.output.limitations
    assert result.resolved_citations == []
