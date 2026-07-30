import pytest

_MACRO_NAMES = (
    "system_instructions",
    "clinical_rules_placeholder",
    "output_format",
    "citation_instructions",
)


@pytest.mark.parametrize(
    "file_name", ["diagnosis.jinja2", "triage.jinja2", "recommendation.jinja2"]
)
def test_template_defines_all_four_macros_with_nonempty_output(jinja_env, file_name):
    module = jinja_env.get_template(file_name).module

    for macro_name in _MACRO_NAMES:
        macro = getattr(module, macro_name)
        assert macro().strip()


def test_diagnosis_template_mentions_diagnosis_language(jinja_env):
    module = jinja_env.get_template("diagnosis.jinja2").module

    assert "diagnosis" in module.output_format().lower()


def test_triage_template_mentions_urgency_language(jinja_env):
    module = jinja_env.get_template("triage.jinja2").module

    assert "triage" in module.output_format().lower()


def test_recommendation_template_mentions_recommendation_language(jinja_env):
    module = jinja_env.get_template("recommendation.jinja2").module

    assert "recommend" in module.output_format().lower()


def test_templates_have_distinct_system_instructions(jinja_env):
    diagnosis = jinja_env.get_template("diagnosis.jinja2").module.system_instructions()
    triage = jinja_env.get_template("triage.jinja2").module.system_instructions()
    recommendation = jinja_env.get_template("recommendation.jinja2").module.system_instructions()

    assert len({diagnosis, triage, recommendation}) == 3


def test_templates_have_distinct_output_formats(jinja_env):
    diagnosis = jinja_env.get_template("diagnosis.jinja2").module.output_format()
    triage = jinja_env.get_template("triage.jinja2").module.output_format()
    recommendation = jinja_env.get_template("recommendation.jinja2").module.output_format()

    assert len({diagnosis, triage, recommendation}) == 3
