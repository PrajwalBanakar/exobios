import pytest

from app.generation.exceptions import GenerationValidationError
from app.generation.models.response import (
    GeneratedRedFlag,
    PossibleCondition,
    RecommendedAction,
    RiskAssessment,
)
from app.generation.validation.response_validator import ResponseValidator
from tests.generation.conftest import make_clinical_draft, make_retrieved_context


def test_valid_draft_resolves_citations_from_trusted_context():
    retrieved_context = make_retrieved_context(citation_numbers=(1,))
    chunk = retrieved_context.groups[0].citations[0].chunk
    draft = make_clinical_draft(citation_numbers=(1,))
    validator = ResponseValidator()

    output = validator.validate_and_resolve(draft, retrieved_context)

    assert len(output.citations) == 1
    resolved = output.citations[0]
    assert resolved.citation_number == 1
    assert resolved.document_id == chunk.document_id
    assert resolved.chunk_id == chunk.chunk_id
    assert resolved.filename == chunk.filename
    assert resolved.page_number == chunk.page_number
    assert resolved.source == chunk.source


def test_unknown_citation_number_is_rejected():
    retrieved_context = make_retrieved_context(citation_numbers=(1,))
    draft = make_clinical_draft(citation_numbers=(1, 99))
    validator = ResponseValidator()

    with pytest.raises(GenerationValidationError, match="99"):
        validator.validate_and_resolve(draft, retrieved_context)


def test_unknown_citation_in_supporting_numbers_is_rejected():
    retrieved_context = make_retrieved_context(citation_numbers=(1,))
    draft = make_clinical_draft(citation_numbers=(1,))
    draft.risk_assessment.supporting_citation_numbers = [1, 42]
    validator = ResponseValidator()

    with pytest.raises(GenerationValidationError, match="42"):
        validator.validate_and_resolve(draft, retrieved_context)


def test_duplicate_possible_conditions_are_rejected():
    retrieved_context = make_retrieved_context()
    draft = make_clinical_draft(
        possible_conditions=[
            PossibleCondition(name="Flu", likelihood="LOW", reasoning="a"),
            PossibleCondition(name="flu", likelihood="MODERATE", reasoning="b"),
        ]
    )
    validator = ResponseValidator()

    with pytest.raises(GenerationValidationError, match="duplicate possible conditions"):
        validator.validate_and_resolve(draft, retrieved_context)


def test_duplicate_red_flags_are_rejected():
    retrieved_context = make_retrieved_context()
    draft = make_clinical_draft(
        red_flags=[
            GeneratedRedFlag(description="Severe chest pain", severity="URGENT", action="ECG"),
            GeneratedRedFlag(
                description="severe chest pain", severity="EMERGENCY", action="ECG now"
            ),
        ],
        risk_assessment=RiskAssessment(
            level="HIGH", reasoning="x", requires_immediate_escalation=True
        ),
    )
    validator = ResponseValidator()

    with pytest.raises(GenerationValidationError, match="duplicate red flags"):
        validator.validate_and_resolve(draft, retrieved_context)


def test_duplicate_recommended_actions_are_rejected():
    retrieved_context = make_retrieved_context()
    draft = make_clinical_draft(
        recommended_actions=[
            RecommendedAction(action="Order CBC", priority="ROUTINE", reasoning="a"),
            RecommendedAction(action="order cbc", priority="SOON", reasoning="b"),
        ]
    )
    validator = ResponseValidator()

    with pytest.raises(GenerationValidationError, match="duplicate recommended actions"):
        validator.validate_and_resolve(draft, retrieved_context)


def test_critical_risk_without_escalation_is_rejected():
    retrieved_context = make_retrieved_context()
    draft = make_clinical_draft(
        risk_assessment=RiskAssessment(
            level="CRITICAL", reasoning="Severe presentation", requires_immediate_escalation=False
        )
    )
    validator = ResponseValidator()

    with pytest.raises(GenerationValidationError, match="CRITICAL"):
        validator.validate_and_resolve(draft, retrieved_context)


def test_critical_risk_with_escalation_is_accepted():
    retrieved_context = make_retrieved_context()
    draft = make_clinical_draft(
        risk_assessment=RiskAssessment(
            level="CRITICAL", reasoning="Severe presentation", requires_immediate_escalation=True
        )
    )
    validator = ResponseValidator()

    output = validator.validate_and_resolve(draft, retrieved_context)

    assert output.risk_assessment.level == "CRITICAL"


def test_emergency_red_flag_without_escalation_is_rejected():
    retrieved_context = make_retrieved_context()
    draft = make_clinical_draft(
        red_flags=[
            GeneratedRedFlag(
                description="Airway compromise", severity="EMERGENCY", action="Call 911"
            )
        ],
        risk_assessment=RiskAssessment(
            level="HIGH", reasoning="x", requires_immediate_escalation=False
        ),
    )
    validator = ResponseValidator()

    with pytest.raises(GenerationValidationError, match="EMERGENCY"):
        validator.validate_and_resolve(draft, retrieved_context)


def test_emergency_red_flag_with_escalation_is_accepted():
    retrieved_context = make_retrieved_context()
    draft = make_clinical_draft(
        red_flags=[
            GeneratedRedFlag(
                description="Airway compromise", severity="EMERGENCY", action="Call 911"
            )
        ],
        risk_assessment=RiskAssessment(
            level="CRITICAL", reasoning="x", requires_immediate_escalation=True
        ),
    )
    validator = ResponseValidator()

    output = validator.validate_and_resolve(draft, retrieved_context)

    assert output.red_flags[0].severity == "EMERGENCY"


def test_empty_possible_conditions_list_is_allowed():
    retrieved_context = make_retrieved_context()
    draft = make_clinical_draft(
        possible_conditions=[],
        citations=[],
        limitations=["Insufficient evidence to identify a likely condition."],
    )
    validator = ResponseValidator()

    output = validator.validate_and_resolve(draft, retrieved_context)

    assert output.possible_conditions == []
    assert output.limitations


@pytest.mark.parametrize(
    "phrase",
    [
        "This is a confirmed diagnosis of pneumonia.",
        "The diagnosis is confirmed based on imaging.",
        "The patient is confirmed to have appendicitis.",
        "We definitively confirms bacterial infection.",
    ],
)
def test_confirmed_diagnosis_wording_in_summary_is_rejected(phrase):
    retrieved_context = make_retrieved_context()
    draft = make_clinical_draft(summary=phrase)
    validator = ResponseValidator()

    with pytest.raises(GenerationValidationError, match="confirmed diagnosis"):
        validator.validate_and_resolve(draft, retrieved_context)


def test_confirmed_diagnosis_wording_in_condition_reasoning_is_rejected():
    retrieved_context = make_retrieved_context()
    draft = make_clinical_draft(
        possible_conditions=[
            PossibleCondition(
                name="Pneumonia",
                likelihood="HIGH",
                reasoning="This is a confirmed diagnosis given the findings.",
            )
        ]
    )
    validator = ResponseValidator()

    with pytest.raises(GenerationValidationError, match="confirmed diagnosis"):
        validator.validate_and_resolve(draft, retrieved_context)


def test_hedged_uncertainty_language_is_not_flagged_as_confirmed_diagnosis():
    retrieved_context = make_retrieved_context()
    draft = make_clinical_draft(
        summary="No diagnosis can be confirmed without further testing; possible viral illness."
    )
    validator = ResponseValidator()

    output = validator.validate_and_resolve(draft, retrieved_context)

    assert output.summary == draft.summary


def test_blank_summary_is_rejected_even_if_whitespace_only():
    retrieved_context = make_retrieved_context()
    draft = make_clinical_draft()
    draft.summary = "   "
    validator = ResponseValidator()

    with pytest.raises(GenerationValidationError, match="blank"):
        validator.validate_and_resolve(draft, retrieved_context)


def test_unexpected_internal_error_is_wrapped_as_generation_validation_error(monkeypatch):
    retrieved_context = make_retrieved_context()
    draft = make_clinical_draft()
    validator = ResponseValidator()
    monkeypatch.setattr(
        validator,
        "_build_citation_index",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    with pytest.raises(GenerationValidationError):
        validator.validate_and_resolve(draft, retrieved_context)
