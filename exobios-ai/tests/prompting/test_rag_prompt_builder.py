import pytest
from jinja2 import DictLoader, Environment

from app.prompting.builders.rag_prompt_builder import RagPromptBuilder, count_tokens
from app.prompting.exceptions import PromptBuildError
from app.prompting.formatting.context_formatter import ContextFormatter
from app.prompting.models.prompt import PromptContext, PromptSectionName, PromptTemplateName
from tests.prompting.conftest import make_patient_context
from tests.retrieval.conftest import make_retrieved_chunk


def _context(chunks=None, **patient_overrides) -> PromptContext:
    patient = make_patient_context(**patient_overrides)
    retrieved_context = ContextFormatter().format(chunks or [])
    return PromptContext(patient=patient, retrieved_context=retrieved_context)


def test_build_produces_all_eight_sections_in_order(jinja_env):
    builder = RagPromptBuilder(jinja_env=jinja_env)

    response = builder.build(_context(), PromptTemplateName.DIAGNOSIS)

    assert [s.name for s in response.sections] == [
        PromptSectionName.SYSTEM_INSTRUCTIONS,
        PromptSectionName.PATIENT_INFORMATION,
        PromptSectionName.VITAL_SIGNS,
        PromptSectionName.SYMPTOMS,
        PromptSectionName.RETRIEVED_KNOWLEDGE,
        PromptSectionName.CLINICAL_RULES_PLACEHOLDER,
        PromptSectionName.OUTPUT_FORMAT,
        PromptSectionName.CITATION_INSTRUCTIONS,
    ]
    assert response.metadata.section_names == [s.name for s in response.sections]


def test_build_uses_template_specific_wording(jinja_env):
    builder = RagPromptBuilder(jinja_env=jinja_env)

    diagnosis = builder.build(_context(), PromptTemplateName.DIAGNOSIS)
    triage = builder.build(_context(), PromptTemplateName.TRIAGE)

    diagnosis_output = next(
        s.content for s in diagnosis.sections if s.name == PromptSectionName.OUTPUT_FORMAT
    )
    triage_output = next(
        s.content for s in triage.sections if s.name == PromptSectionName.OUTPUT_FORMAT
    )
    assert diagnosis_output != triage_output
    assert diagnosis.metadata.template == PromptTemplateName.DIAGNOSIS
    assert triage.metadata.template == PromptTemplateName.TRIAGE


def test_patient_information_includes_complaint_and_category(jinja_env):
    builder = RagPromptBuilder(jinja_env=jinja_env)
    context = _context(patient_complaint="chest pain", complaint_category=None)

    response = builder.build(context, PromptTemplateName.DIAGNOSIS)

    section = next(
        s for s in response.sections if s.name == PromptSectionName.PATIENT_INFORMATION
    )
    assert "chest pain" in section.content
    assert str(context.patient.assessment_id) in section.content


def test_vital_signs_formats_present_fields(jinja_env):
    builder = RagPromptBuilder(jinja_env=jinja_env)

    response = builder.build(_context(), PromptTemplateName.DIAGNOSIS)

    section = next(s for s in response.sections if s.name == PromptSectionName.VITAL_SIGNS)
    assert "Heart rate: 90 bpm" in section.content
    assert "SpO2: 97.0%" in section.content


def test_vital_signs_handles_missing_vitals(jinja_env):
    builder = RagPromptBuilder(jinja_env=jinja_env)
    context = _context(vitals=None)

    response = builder.build(context, PromptTemplateName.DIAGNOSIS)

    section = next(s for s in response.sections if s.name == PromptSectionName.VITAL_SIGNS)
    assert section.content == "No vital signs recorded."


def test_symptoms_formats_list(jinja_env):
    builder = RagPromptBuilder(jinja_env=jinja_env)

    response = builder.build(_context(), PromptTemplateName.DIAGNOSIS)

    section = next(s for s in response.sections if s.name == PromptSectionName.SYMPTOMS)
    assert "fever" in section.content
    assert "duration: 2 days" in section.content


def test_symptoms_handles_empty_list(jinja_env):
    builder = RagPromptBuilder(jinja_env=jinja_env)
    context = _context(symptoms=[])

    response = builder.build(context, PromptTemplateName.DIAGNOSIS)

    section = next(s for s in response.sections if s.name == PromptSectionName.SYMPTOMS)
    assert section.content == "No symptoms recorded."


def test_retrieved_knowledge_includes_citation_numbers_and_sources(jinja_env):
    chunk = make_retrieved_chunk(text="Fever is common.", filename="guide.pdf", source="who")
    builder = RagPromptBuilder(jinja_env=jinja_env)

    response = builder.build(_context(chunks=[chunk]), PromptTemplateName.DIAGNOSIS)

    section = next(
        s for s in response.sections if s.name == PromptSectionName.RETRIEVED_KNOWLEDGE
    )
    assert "[1] Fever is common." in section.content
    assert "guide.pdf" in section.content
    assert "who" in section.content


def test_retrieved_knowledge_handles_empty_context(jinja_env):
    builder = RagPromptBuilder(jinja_env=jinja_env)

    response = builder.build(_context(chunks=[]), PromptTemplateName.DIAGNOSIS)

    section = next(
        s for s in response.sections if s.name == PromptSectionName.RETRIEVED_KNOWLEDGE
    )
    assert section.content == "No relevant medical knowledge was retrieved."


def test_token_budget_keeps_all_chunks_when_under_budget(jinja_env):
    chunks = [make_retrieved_chunk(score=0.9 - i * 0.1, text="short text") for i in range(3)]
    builder = RagPromptBuilder(jinja_env=jinja_env, max_context_tokens=1000)

    response = builder.build(_context(chunks=chunks), PromptTemplateName.DIAGNOSIS)

    assert response.statistics.included_chunk_count == 3
    assert response.statistics.discarded_chunk_count == 0


def test_token_budget_trims_lowest_ranked_chunks_first(jinja_env):
    long_text = "word " * 100  # ~125 tokens each at 4 chars/token
    chunks = [
        make_retrieved_chunk(score=0.9, text=long_text),
        make_retrieved_chunk(score=0.7, text=long_text),
        make_retrieved_chunk(score=0.5, text=long_text),
    ]
    # Budget fits exactly one chunk's worth of tokens.
    budget = count_tokens(long_text)
    builder = RagPromptBuilder(jinja_env=jinja_env, max_context_tokens=budget)

    response = builder.build(_context(chunks=chunks), PromptTemplateName.DIAGNOSIS)

    assert response.statistics.included_chunk_count == 1
    assert response.statistics.discarded_chunk_count == 2
    assert response.statistics.retrieved_chunk_count == 3
    section = next(
        s for s in response.sections if s.name == PromptSectionName.RETRIEVED_KNOWLEDGE
    )
    assert "[1]" in section.content
    assert "[2]" not in section.content
    assert "[3]" not in section.content


def test_token_budget_of_zero_discards_all_chunks(jinja_env):
    chunks = [make_retrieved_chunk(score=0.9, text="some content")]
    builder = RagPromptBuilder(jinja_env=jinja_env, max_context_tokens=0)

    response = builder.build(_context(chunks=chunks), PromptTemplateName.DIAGNOSIS)

    assert response.statistics.included_chunk_count == 0
    assert response.statistics.discarded_chunk_count == 1


def test_statistics_report_configured_token_budgets(jinja_env):
    builder = RagPromptBuilder(
        jinja_env=jinja_env,
        max_prompt_tokens=1234,
        max_context_tokens=500,
        reserved_response_tokens=99,
    )

    response = builder.build(_context(), PromptTemplateName.DIAGNOSIS)

    assert response.statistics.max_prompt_tokens == 1234
    assert response.statistics.reserved_response_tokens == 99


def test_unknown_template_raises_prompt_build_error(jinja_env):
    builder = RagPromptBuilder(jinja_env=jinja_env)

    with pytest.raises(PromptBuildError):
        builder.build(_context(), "not-a-real-template")


def test_build_wraps_template_missing_macro_as_prompt_build_error():
    template_source = "{% macro system_instructions() %}hi{% endmacro %}"
    env = Environment(
        loader=DictLoader({"diagnosis.jinja2": template_source}),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    builder = RagPromptBuilder(jinja_env=env)

    with pytest.raises(PromptBuildError):
        builder.build(_context(), PromptTemplateName.DIAGNOSIS)


def test_count_tokens_empty_string_is_zero():
    assert count_tokens("") == 0


def test_count_tokens_is_roughly_chars_over_four():
    assert count_tokens("a" * 40) == 10
