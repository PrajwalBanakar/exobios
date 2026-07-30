from datetime import UTC, datetime

from jinja2 import Environment

from app.prompting.builders.base import PromptBuilder
from app.prompting.exceptions import PromptBuildError
from app.prompting.models.prompt import (
    PatientContext,
    PromptContext,
    PromptMetadata,
    PromptResponse,
    PromptSection,
    PromptSectionName,
    PromptStatistics,
    PromptTemplate,
    PromptTemplateName,
    RetrievedContext,
)
from app.schemas.analyze import SymptomSummary, VitalsSummary

_TEMPLATE_FILES: dict[PromptTemplateName, str] = {
    PromptTemplateName.DIAGNOSIS: "diagnosis.jinja2",
    PromptTemplateName.TRIAGE: "triage.jinja2",
    PromptTemplateName.RECOMMENDATION: "recommendation.jinja2",
}

_SECTION_TITLES: dict[PromptSectionName, str] = {
    PromptSectionName.SYSTEM_INSTRUCTIONS: "System Instructions",
    PromptSectionName.PATIENT_INFORMATION: "Patient Information",
    PromptSectionName.VITAL_SIGNS: "Vital Signs",
    PromptSectionName.SYMPTOMS: "Symptoms",
    PromptSectionName.RETRIEVED_KNOWLEDGE: "Retrieved Medical Knowledge",
    PromptSectionName.CLINICAL_RULES_PLACEHOLDER: "Clinical Rules",
    PromptSectionName.OUTPUT_FORMAT: "Expected Output Format",
    PromptSectionName.CITATION_INSTRUCTIONS: "Citation Instructions",
}


def count_tokens(text: str) -> int:
    """Approximate token count using the ~4-characters-per-token heuristic
    commonly used for English text with GPT-style tokenizers. Deliberately
    not tied to any specific provider's real tokenizer (see factory.py
    extension notes) — this stays provider-agnostic and needs no network
    access to a tokenizer's vocabulary file.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


class RagPromptBuilder(PromptBuilder):
    """Assembles a complete RAG prompt from a PromptContext: system
    instructions, patient information, vital signs, symptoms, retrieved
    medical knowledge (token-budget-trimmed to the highest-ranked chunks),
    a clinical-rules placeholder, the expected output format, and citation
    instructions — in that order.

    The four sections whose wording depends on the use case (system
    instructions, clinical rules placeholder, output format, citation
    instructions) are defined as Jinja2 macros in the selected template
    file. The four data-driven sections (patient info, vitals, symptoms,
    retrieved knowledge), whose *structure* doesn't vary by use case, are
    formatted directly from the Pydantic models in Python.
    """

    def __init__(
        self,
        jinja_env: Environment,
        max_prompt_tokens: int = 4000,
        max_context_tokens: int = 2000,
        reserved_response_tokens: int = 500,
    ) -> None:
        self._env = jinja_env
        self._max_prompt_tokens = max_prompt_tokens
        self._max_context_tokens = max_context_tokens
        self._reserved_response_tokens = reserved_response_tokens

    def build(self, context: PromptContext, template: PromptTemplateName) -> PromptResponse:
        prompt_template = self._resolve_template(template)

        try:
            module = self._env.get_template(prompt_template.file_name).module
        except Exception as exc:
            raise PromptBuildError(reason=str(exc)) from exc

        trimmed_context, context_tokens = self._apply_context_budget(context.retrieved_context)

        try:
            sections = [
                self._make_section(
                    PromptSectionName.SYSTEM_INSTRUCTIONS, module.system_instructions().strip()
                ),
                self._make_section(
                    PromptSectionName.PATIENT_INFORMATION,
                    self._format_patient_information(context.patient),
                ),
                self._make_section(
                    PromptSectionName.VITAL_SIGNS, self._format_vital_signs(context.patient.vitals)
                ),
                self._make_section(
                    PromptSectionName.SYMPTOMS, self._format_symptoms(context.patient.symptoms)
                ),
                self._make_section(
                    PromptSectionName.RETRIEVED_KNOWLEDGE,
                    self._format_retrieved_knowledge(trimmed_context),
                ),
                self._make_section(
                    PromptSectionName.CLINICAL_RULES_PLACEHOLDER,
                    module.clinical_rules_placeholder().strip(),
                ),
                self._make_section(
                    PromptSectionName.OUTPUT_FORMAT, module.output_format().strip()
                ),
                self._make_section(
                    PromptSectionName.CITATION_INSTRUCTIONS, module.citation_instructions().strip()
                ),
            ]
        except PromptBuildError:
            raise
        except Exception as exc:
            raise PromptBuildError(reason=str(exc)) from exc

        prompt_text = "\n\n".join(
            f"## {_SECTION_TITLES[section.name]}\n{section.content}" for section in sections
        )

        metadata = PromptMetadata(
            assessment_id=context.patient.assessment_id,
            template=template,
            created_at=datetime.now(UTC),
            section_names=[section.name for section in sections],
            citation_count=trimmed_context.total_chunks,
        )
        statistics = PromptStatistics(
            prompt_tokens=count_tokens(prompt_text),
            context_tokens=context_tokens,
            reserved_response_tokens=self._reserved_response_tokens,
            max_prompt_tokens=self._max_prompt_tokens,
            retrieved_chunk_count=context.retrieved_context.total_chunks,
            included_chunk_count=trimmed_context.total_chunks,
            discarded_chunk_count=trimmed_context.discarded_chunk_count,
        )

        return PromptResponse(
            prompt=prompt_text,
            sections=sections,
            metadata=metadata,
            statistics=statistics,
            retrieved_context=trimmed_context,
        )

    def _resolve_template(self, template: PromptTemplateName) -> PromptTemplate:
        file_name = _TEMPLATE_FILES.get(template)
        if file_name is None:
            raise PromptBuildError(reason=f"Unknown prompt template '{template}'")
        return PromptTemplate(name=template, file_name=file_name)

    def _apply_context_budget(
        self, retrieved_context: RetrievedContext
    ) -> tuple[RetrievedContext, int]:
        flat = sorted(
            (cited for group in retrieved_context.groups for cited in group.citations),
            key=lambda cited: cited.citation_number,
        )

        kept_citation_numbers: set[int] = set()
        used_tokens = 0
        for cited in flat:
            tokens = count_tokens(cited.chunk.text)
            if used_tokens + tokens > self._max_context_tokens:
                # Strict cutoff: everything from here on is lower-ranked
                # (flat is relevance-ordered), so it's all discarded too —
                # a later, smaller chunk never jumps ahead of a larger,
                # more relevant one.
                break
            used_tokens += tokens
            kept_citation_numbers.add(cited.citation_number)

        trimmed_groups = []
        for group in retrieved_context.groups:
            kept = [c for c in group.citations if c.citation_number in kept_citation_numbers]
            if kept:
                trimmed_groups.append(group.model_copy(update={"citations": kept}))

        discarded = len(flat) - len(kept_citation_numbers)
        trimmed = RetrievedContext(
            groups=trimmed_groups,
            total_chunks=len(kept_citation_numbers),
            discarded_chunk_count=retrieved_context.discarded_chunk_count + discarded,
        )
        return trimmed, used_tokens

    def _make_section(self, name: PromptSectionName, content: str) -> PromptSection:
        return PromptSection(name=name, content=content, token_count=count_tokens(content))

    def _format_patient_information(self, patient: PatientContext) -> str:
        lines = [f"Assessment ID: {patient.assessment_id}", f"Patient ID: {patient.patient_id}"]
        if patient.patient_complaint:
            lines.append(f"Chief complaint: {patient.patient_complaint}")
        if patient.complaint_category:
            lines.append(f"Complaint category: {patient.complaint_category}")
        if patient.past_illnesses:
            lines.append(f"Past illnesses: {patient.past_illnesses}")
        if patient.current_medications:
            lines.append(f"Current medications: {patient.current_medications}")
        if patient.allergies:
            lines.append(f"Allergies: {patient.allergies}")
        return "\n".join(lines)

    def _format_vital_signs(self, vitals: VitalsSummary | None) -> str:
        if vitals is None:
            return "No vital signs recorded."

        lines = []
        if vitals.heart_rate is not None:
            lines.append(f"Heart rate: {vitals.heart_rate} bpm")
        if vitals.spo2 is not None:
            lines.append(f"SpO2: {vitals.spo2}%")
        if vitals.temperature is not None:
            lines.append(f"Temperature: {vitals.temperature} C")
        systolic = vitals.blood_pressure_systolic
        diastolic = vitals.blood_pressure_diastolic
        if systolic is not None and diastolic is not None:
            lines.append(f"Blood pressure: {systolic}/{diastolic} mmHg")
        if vitals.respiratory_rate is not None:
            lines.append(f"Respiratory rate: {vitals.respiratory_rate} breaths/min")

        return "\n".join(lines) if lines else "No vital signs recorded."

    def _format_symptoms(self, symptoms: list[SymptomSummary]) -> str:
        if not symptoms:
            return "No symptoms recorded."

        lines = []
        for symptom in symptoms:
            parts = [symptom.name]
            if symptom.duration:
                parts.append(f"duration: {symptom.duration}")
            if symptom.severity:
                parts.append(f"severity: {symptom.severity}")
            lines.append("- " + ", ".join(parts))
        return "\n".join(lines)

    def _format_retrieved_knowledge(self, retrieved_context: RetrievedContext) -> str:
        if not retrieved_context.groups:
            return "No relevant medical knowledge was retrieved."

        blocks = []
        for group in retrieved_context.groups:
            header = f"Source: {group.filename} ({group.document_type.value}, {group.source})"
            citation_lines = [f"[{c.citation_number}] {c.chunk.text}" for c in group.citations]
            blocks.append(header + "\n" + "\n".join(citation_lines))
        return "\n\n".join(blocks)
