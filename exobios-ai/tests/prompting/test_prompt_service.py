from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.embeddings.exceptions import EmbeddingGenerationError
from app.prompting.exceptions import ContextFormattingError, PromptBuildError
from app.prompting.models.prompt import (
    PromptMetadata,
    PromptRequest,
    PromptResponse,
    PromptStatistics,
    PromptTemplateName,
    RetrievedContext,
)
from app.prompting.services.prompt_service import PromptService
from app.retrieval.exceptions import RetrievalError, SearchError
from app.retrieval.models.retrieval import SearchRequest, SearchResponse
from tests.prompting.conftest import (
    FakeContextFormatter,
    FakePromptBuilder,
    FakeRetrievalService,
    make_patient_context,
)
from tests.retrieval.conftest import make_retrieved_chunk


def _request(**overrides) -> PromptRequest:
    defaults = {
        "patient": make_patient_context(),
        "search_request": SearchRequest(query="fever and cough"),
        "template": None,
    }
    defaults.update(overrides)
    return PromptRequest(**defaults)


def _minimal_retrieved_context() -> RetrievedContext:
    return RetrievedContext(groups=[], total_chunks=0)


def _minimal_prompt_response(assessment_id: UUID) -> PromptResponse:
    return PromptResponse(
        prompt="a prompt",
        sections=[],
        metadata=PromptMetadata(
            assessment_id=assessment_id,
            template=PromptTemplateName.DIAGNOSIS,
            created_at=datetime.now(UTC),
            section_names=[],
            citation_count=0,
        ),
        statistics=PromptStatistics(
            prompt_tokens=10,
            context_tokens=0,
            reserved_response_tokens=500,
            max_prompt_tokens=4000,
            retrieved_chunk_count=0,
            included_chunk_count=0,
            discarded_chunk_count=0,
        ),
        retrieved_context=_minimal_retrieved_context(),
    )


def test_build_prompt_happy_path_calls_each_stage_in_order():
    chunk = make_retrieved_chunk()
    patient = make_patient_context()
    retrieval = FakeRetrievalService(
        response=SearchResponse(query="q", results=[chunk], result_count=1, elapsed_ms=1.0)
    )
    formatter_response = _minimal_retrieved_context()
    formatter = FakeContextFormatter(response=formatter_response)
    builder_response = _minimal_prompt_response(patient.assessment_id)
    builder = FakePromptBuilder(response=builder_response)
    service = PromptService(
        retrieval_service=retrieval, prompt_builder=builder, context_formatter=formatter
    )

    result = service.build_prompt(_request(patient=patient))

    assert result is builder_response
    assert formatter.calls == [[chunk]]
    assert len(builder.calls) == 1
    prompt_context, template = builder.calls[0]
    assert prompt_context.retrieved_context is formatter_response
    assert template == PromptTemplateName.DIAGNOSIS


def test_build_prompt_uses_default_template_when_request_omits_one():
    patient = make_patient_context()
    retrieval = FakeRetrievalService(
        response=SearchResponse(query="q", results=[], result_count=0, elapsed_ms=0.0)
    )
    formatter = FakeContextFormatter(response=_minimal_retrieved_context())
    builder = FakePromptBuilder(response=_minimal_prompt_response(patient.assessment_id))
    service = PromptService(
        retrieval_service=retrieval,
        prompt_builder=builder,
        context_formatter=formatter,
        default_template=PromptTemplateName.TRIAGE,
    )

    service.build_prompt(_request(patient=patient, template=None))

    _, template = builder.calls[0]
    assert template == PromptTemplateName.TRIAGE


def test_build_prompt_uses_request_template_override():
    patient = make_patient_context()
    retrieval = FakeRetrievalService(
        response=SearchResponse(query="q", results=[], result_count=0, elapsed_ms=0.0)
    )
    formatter = FakeContextFormatter(response=_minimal_retrieved_context())
    builder = FakePromptBuilder(response=_minimal_prompt_response(patient.assessment_id))
    service = PromptService(
        retrieval_service=retrieval,
        prompt_builder=builder,
        context_formatter=formatter,
        default_template=PromptTemplateName.DIAGNOSIS,
    )

    service.build_prompt(_request(patient=patient, template=PromptTemplateName.RECOMMENDATION))

    _, template = builder.calls[0]
    assert template == PromptTemplateName.RECOMMENDATION


@pytest.mark.parametrize(
    "exc",
    [
        RetrievalError(reason="down"),
        SearchError(reason="down"),
        EmbeddingGenerationError(reason="rate limited"),
    ],
)
def test_build_prompt_propagates_known_retrieval_errors(exc):
    retrieval = FakeRetrievalService(fail_with=exc)
    formatter = FakeContextFormatter()
    builder = FakePromptBuilder()
    service = PromptService(
        retrieval_service=retrieval, prompt_builder=builder, context_formatter=formatter
    )

    with pytest.raises(type(exc)):
        service.build_prompt(_request())


def test_build_prompt_wraps_unexpected_retrieval_exception_as_prompt_build_error():
    retrieval = FakeRetrievalService(fail_with=RuntimeError("boom"))
    formatter = FakeContextFormatter()
    builder = FakePromptBuilder()
    service = PromptService(
        retrieval_service=retrieval, prompt_builder=builder, context_formatter=formatter
    )

    with pytest.raises(PromptBuildError):
        service.build_prompt(_request())


def test_build_prompt_propagates_context_formatting_error():
    retrieval = FakeRetrievalService(
        response=SearchResponse(query="q", results=[], result_count=0, elapsed_ms=0.0)
    )
    formatter = FakeContextFormatter(fail_with=ContextFormattingError(reason="bad data"))
    builder = FakePromptBuilder()
    service = PromptService(
        retrieval_service=retrieval, prompt_builder=builder, context_formatter=formatter
    )

    with pytest.raises(ContextFormattingError):
        service.build_prompt(_request())


def test_build_prompt_wraps_unexpected_formatting_exception():
    retrieval = FakeRetrievalService(
        response=SearchResponse(query="q", results=[], result_count=0, elapsed_ms=0.0)
    )
    formatter = FakeContextFormatter(fail_with=RuntimeError("boom"))
    builder = FakePromptBuilder()
    service = PromptService(
        retrieval_service=retrieval, prompt_builder=builder, context_formatter=formatter
    )

    with pytest.raises(ContextFormattingError):
        service.build_prompt(_request())


def test_build_prompt_propagates_prompt_build_error_from_builder():
    retrieval = FakeRetrievalService(
        response=SearchResponse(query="q", results=[], result_count=0, elapsed_ms=0.0)
    )
    formatter = FakeContextFormatter(response=_minimal_retrieved_context())
    builder = FakePromptBuilder(fail_with=PromptBuildError(reason="template broke"))
    service = PromptService(
        retrieval_service=retrieval, prompt_builder=builder, context_formatter=formatter
    )

    with pytest.raises(PromptBuildError):
        service.build_prompt(_request())


def test_build_prompt_wraps_unexpected_builder_exception():
    retrieval = FakeRetrievalService(
        response=SearchResponse(query="q", results=[], result_count=0, elapsed_ms=0.0)
    )
    formatter = FakeContextFormatter(response=_minimal_retrieved_context())
    builder = FakePromptBuilder(fail_with=RuntimeError("boom"))
    service = PromptService(
        retrieval_service=retrieval, prompt_builder=builder, context_formatter=formatter
    )

    with pytest.raises(PromptBuildError):
        service.build_prompt(_request())


def test_logs_each_pipeline_stage(caplog):
    patient = make_patient_context()
    response = _minimal_prompt_response(patient.assessment_id)
    retrieval = FakeRetrievalService(
        response=SearchResponse(query="q", results=[], result_count=0, elapsed_ms=0.0)
    )
    formatter = FakeContextFormatter(response=_minimal_retrieved_context())
    builder = FakePromptBuilder(response=response)
    service = PromptService(
        retrieval_service=retrieval, prompt_builder=builder, context_formatter=formatter
    )

    with caplog.at_level("INFO", logger="app.prompting"):
        service.build_prompt(_request(patient=patient))

    messages = " ".join(record.message for record in caplog.records)
    for expected in (
        "prompt_started",
        "context_retrieved",
        "context_formatted",
        "prompt_built",
        "prompt_completed",
    ):
        assert expected in messages


def test_logs_prompt_failed_on_retrieval_error(caplog):
    retrieval = FakeRetrievalService(fail_with=RuntimeError("boom"))
    formatter = FakeContextFormatter()
    builder = FakePromptBuilder()
    service = PromptService(
        retrieval_service=retrieval, prompt_builder=builder, context_formatter=formatter
    )

    with caplog.at_level("ERROR", logger="app.prompting"), pytest.raises(PromptBuildError):
        service.build_prompt(_request())

    assert any("prompt_failed" in record.message for record in caplog.records)


def test_logs_prompt_failed_on_formatting_error(caplog):
    retrieval = FakeRetrievalService(
        response=SearchResponse(query="q", results=[], result_count=0, elapsed_ms=0.0)
    )
    formatter = FakeContextFormatter(fail_with=RuntimeError("boom"))
    builder = FakePromptBuilder()
    service = PromptService(
        retrieval_service=retrieval, prompt_builder=builder, context_formatter=formatter
    )

    with caplog.at_level("ERROR", logger="app.prompting"), pytest.raises(ContextFormattingError):
        service.build_prompt(_request())

    assert any("prompt_failed" in record.message for record in caplog.records)


def test_logs_prompt_failed_on_build_error(caplog):
    retrieval = FakeRetrievalService(
        response=SearchResponse(query="q", results=[], result_count=0, elapsed_ms=0.0)
    )
    formatter = FakeContextFormatter(response=_minimal_retrieved_context())
    builder = FakePromptBuilder(fail_with=RuntimeError("boom"))
    service = PromptService(
        retrieval_service=retrieval, prompt_builder=builder, context_formatter=formatter
    )

    with caplog.at_level("ERROR", logger="app.prompting"), pytest.raises(PromptBuildError):
        service.build_prompt(_request())

    assert any("prompt_failed" in record.message for record in caplog.records)
