from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.generation.models.request import GenerationParameters, GenerationRequest
from app.generation.models.response import (
    CitationReference,
    ClinicalGenerationDraft,
    GeneratedRedFlag,
    PossibleCondition,
    RecommendedAction,
    RiskAssessment,
)
from app.generation.models.usage import TokenUsage
from tests.generation.conftest import make_clinical_draft, make_prompt_response


def test_clinical_generation_draft_valid_construction():
    draft = make_clinical_draft()

    assert draft.summary
    assert draft.citations == [1]


def test_possible_condition_rejects_invalid_likelihood_enum():
    with pytest.raises(ValidationError):
        PossibleCondition(name="Flu", likelihood="SUPER_HIGH", reasoning="x")


def test_risk_assessment_rejects_invalid_level_enum():
    with pytest.raises(ValidationError):
        RiskAssessment(level="SEVERE", reasoning="x", requires_immediate_escalation=False)


def test_red_flag_rejects_invalid_severity_enum():
    with pytest.raises(ValidationError):
        GeneratedRedFlag(description="x", severity="CRITICAL", action="x")


def test_recommended_action_rejects_invalid_priority_enum():
    with pytest.raises(ValidationError):
        RecommendedAction(action="x", priority="ASAP", reasoning="x")


def test_clinical_generation_draft_requires_summary():
    with pytest.raises(ValidationError):
        make_clinical_draft(summary=None)


def test_clinical_generation_draft_rejects_empty_summary():
    with pytest.raises(ValidationError):
        make_clinical_draft(summary="")


def test_clinical_generation_draft_requires_risk_assessment():
    with pytest.raises(ValidationError):
        ClinicalGenerationDraft(summary="x", risk_assessment=None)


def test_possible_condition_rejects_empty_name():
    with pytest.raises(ValidationError):
        PossibleCondition(name="", likelihood="LOW", reasoning="x")


def test_risk_assessment_rejects_empty_reasoning():
    with pytest.raises(ValidationError):
        RiskAssessment(level="LOW", reasoning="", requires_immediate_escalation=False)


def test_citation_reference_page_number_is_optional():
    with_page = CitationReference(
        citation_number=1,
        document_id=uuid4(),
        chunk_id=uuid4(),
        filename="a.pdf",
        page_number=3,
        source="textbook",
    )
    without_page = CitationReference(
        citation_number=1,
        document_id=uuid4(),
        chunk_id=uuid4(),
        filename="a.docx",
        page_number=None,
        source="textbook",
    )
    assert with_page.page_number == 3
    assert without_page.page_number is None


def test_citation_reference_requires_document_id():
    with pytest.raises(ValidationError):
        CitationReference(
            citation_number=1,
            document_id=None,
            chunk_id=uuid4(),
            filename="a.pdf",
            source="textbook",
        )


def test_clinical_generation_draft_allows_empty_possible_conditions_for_insufficient_evidence():
    draft = make_clinical_draft(
        possible_conditions=[],
        citations=[],
        limitations=["Insufficient evidence to suggest any specific condition."],
    )

    assert draft.possible_conditions == []
    assert draft.limitations


def test_clinical_generation_draft_allows_empty_red_flags_and_actions():
    draft = make_clinical_draft(red_flags=[], recommended_actions=[])

    assert draft.red_flags == []
    assert draft.recommended_actions == []


def test_generation_parameters_rejects_temperature_out_of_bounds():
    with pytest.raises(ValidationError):
        GenerationParameters(temperature=2.5)
    with pytest.raises(ValidationError):
        GenerationParameters(temperature=-0.1)


def test_generation_parameters_accepts_boundary_temperatures():
    assert GenerationParameters(temperature=0.0).temperature == 0.0
    assert GenerationParameters(temperature=2.0).temperature == 2.0


def test_generation_parameters_rejects_non_positive_max_output_tokens():
    with pytest.raises(ValidationError):
        GenerationParameters(max_output_tokens=0)


def test_generation_request_generates_a_request_id_by_default():
    generation_request = GenerationRequest(prompt_response=make_prompt_response())

    assert generation_request.request_id
    assert generation_request.model is None
    assert generation_request.parameters == GenerationParameters()


def test_generation_request_accepts_explicit_overrides():
    generation_request = GenerationRequest(
        prompt_response=make_prompt_response(),
        model="gpt-4.1",
        parameters=GenerationParameters(temperature=0.5),
        request_id="corr-123",
    )

    assert generation_request.model == "gpt-4.1"
    assert generation_request.parameters.temperature == 0.5
    assert generation_request.request_id == "corr-123"


def test_token_usage_rejects_negative_values():
    with pytest.raises(ValidationError):
        TokenUsage(input_tokens=-1, output_tokens=0, total_tokens=0)
