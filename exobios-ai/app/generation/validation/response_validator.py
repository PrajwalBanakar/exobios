import re

from app.generation.exceptions import GenerationValidationError
from app.generation.models.response import (
    CitationReference,
    ClinicalGenerationDraft,
    ClinicalGenerationOutput,
    RedFlagSeverity,
)
from app.prompting.models.prompt import CitedChunk, RetrievedContext
from app.schemas.analyze import RiskLevel

# Deliberately narrow: only phrases that assert a diagnosis has been
# *confirmed*. Broader matching (e.g. bare "diagnosis") would false-positive
# on legitimate, hedged language like "no diagnosis can be confirmed" or
# "possible diagnosis". This is a best-effort deterministic backstop, not a
# substitute for the prompt's own instructions — see response.py's docstring
# and the deliverables notes on this being "reasonably detectable", not
# exhaustive.
_CONFIRMED_DIAGNOSIS_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bconfirmed diagnosis\b",
        r"\bdiagnosis (?:is|has been) confirmed\b",
        r"\bdefinitive(?:ly)? diagnos\w*\b",
        r"\bis confirmed to have\b",
        r"\bdefinitively confirms?\b",
    ]
]


class ResponseValidator:
    """Deterministic, Python-only validation of a ClinicalGenerationDraft
    against the trusted RetrievedContext it was generated from. Never asks
    the LLM to validate itself — every check here is plain Python.

    Citation numbers are the only thing trusted from the model. Every
    CitationReference's metadata (document_id, chunk_id, filename,
    page_number, source) is resolved here from RetrievedContext, never from
    the model's output.
    """

    def validate_and_resolve(
        self, draft: ClinicalGenerationDraft, retrieved_context: RetrievedContext
    ) -> ClinicalGenerationOutput:
        try:
            return self._validate_and_resolve(draft, retrieved_context)
        except GenerationValidationError:
            raise
        except Exception as exc:
            raise GenerationValidationError(reason=str(exc)) from exc

    def _validate_and_resolve(
        self, draft: ClinicalGenerationDraft, retrieved_context: RetrievedContext
    ) -> ClinicalGenerationOutput:
        self._validate_summary(draft)
        self._validate_no_duplicate_conditions(draft)
        self._validate_no_duplicate_red_flags(draft)
        self._validate_no_duplicate_actions(draft)
        self._validate_no_confirmed_diagnosis_wording(draft)
        self._validate_critical_risk_escalation(draft)
        self._validate_emergency_red_flag_escalation(draft)

        citation_index = self._build_citation_index(retrieved_context)
        self._validate_citation_numbers(draft, citation_index)
        resolved_citations = self._resolve_citations(draft.citations, citation_index)

        return ClinicalGenerationOutput(
            summary=draft.summary,
            possible_conditions=draft.possible_conditions,
            risk_assessment=draft.risk_assessment,
            red_flags=draft.red_flags,
            recommended_actions=draft.recommended_actions,
            follow_up_questions=draft.follow_up_questions,
            citations=resolved_citations,
            limitations=draft.limitations,
        )

    def _validate_summary(self, draft: ClinicalGenerationDraft) -> None:
        if not draft.summary.strip():
            raise GenerationValidationError(reason="summary must not be blank")

    def _validate_no_duplicate_conditions(self, draft: ClinicalGenerationDraft) -> None:
        names = [c.name.strip().lower() for c in draft.possible_conditions]
        duplicates = self._find_duplicates(names)
        if duplicates:
            raise GenerationValidationError(
                reason=f"duplicate possible conditions: {sorted(duplicates)}"
            )

    def _validate_no_duplicate_red_flags(self, draft: ClinicalGenerationDraft) -> None:
        descriptions = [f.description.strip().lower() for f in draft.red_flags]
        duplicates = self._find_duplicates(descriptions)
        if duplicates:
            raise GenerationValidationError(reason=f"duplicate red flags: {sorted(duplicates)}")

    def _validate_no_duplicate_actions(self, draft: ClinicalGenerationDraft) -> None:
        actions = [a.action.strip().lower() for a in draft.recommended_actions]
        duplicates = self._find_duplicates(actions)
        if duplicates:
            raise GenerationValidationError(
                reason=f"duplicate recommended actions: {sorted(duplicates)}"
            )

    def _find_duplicates(self, values: list[str]) -> set[str]:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for value in values:
            if value in seen:
                duplicates.add(value)
            seen.add(value)
        return duplicates

    def _validate_no_confirmed_diagnosis_wording(self, draft: ClinicalGenerationDraft) -> None:
        texts = [draft.summary, draft.risk_assessment.reasoning]
        texts.extend(condition.reasoning for condition in draft.possible_conditions)
        for text in texts:
            for pattern in _CONFIRMED_DIAGNOSIS_PATTERNS:
                if pattern.search(text):
                    raise GenerationValidationError(
                        reason=(
                            "output claims a confirmed diagnosis "
                            f"(matched {pattern.pattern!r}); possible conditions must be "
                            "presented as possibilities, not confirmed diagnoses"
                        )
                    )

    def _validate_critical_risk_escalation(self, draft: ClinicalGenerationDraft) -> None:
        if (
            draft.risk_assessment.level == RiskLevel.CRITICAL
            and not draft.risk_assessment.requires_immediate_escalation
        ):
            raise GenerationValidationError(
                reason="risk_assessment.level=CRITICAL requires requires_immediate_escalation=true"
            )

    def _validate_emergency_red_flag_escalation(self, draft: ClinicalGenerationDraft) -> None:
        has_emergency_flag = any(
            flag.severity == RedFlagSeverity.EMERGENCY for flag in draft.red_flags
        )
        if has_emergency_flag and not draft.risk_assessment.requires_immediate_escalation:
            raise GenerationValidationError(
                reason=(
                    "an EMERGENCY red flag requires "
                    "risk_assessment.requires_immediate_escalation=true"
                )
            )

    def _build_citation_index(self, retrieved_context: RetrievedContext) -> dict[int, CitedChunk]:
        return {
            cited.citation_number: cited
            for group in retrieved_context.groups
            for cited in group.citations
        }

    def _validate_citation_numbers(
        self, draft: ClinicalGenerationDraft, citation_index: dict[int, CitedChunk]
    ) -> None:
        referenced: set[int] = set(draft.citations)
        for condition in draft.possible_conditions:
            referenced.update(condition.supporting_citation_numbers)
        referenced.update(draft.risk_assessment.supporting_citation_numbers)
        for flag in draft.red_flags:
            referenced.update(flag.supporting_citation_numbers)
        for action in draft.recommended_actions:
            referenced.update(action.supporting_citation_numbers)

        invalid = referenced - citation_index.keys()
        if invalid:
            # Preferred policy (explicit, per spec): invalid citations fail
            # validation outright — they are never silently dropped or
            # substituted, since that could mask the model inventing a
            # source.
            raise GenerationValidationError(
                reason=f"response cited unknown citation numbers: {sorted(invalid)}"
            )

    def _resolve_citations(
        self, citation_numbers: list[int], citation_index: dict[int, CitedChunk]
    ) -> list[CitationReference]:
        resolved: list[CitationReference] = []
        seen: set[int] = set()
        for number in citation_numbers:
            if number in seen:
                continue
            seen.add(number)
            cited = citation_index[number]
            resolved.append(
                CitationReference(
                    citation_number=number,
                    document_id=cited.chunk.document_id,
                    chunk_id=cited.chunk.chunk_id,
                    filename=cited.chunk.filename,
                    page_number=cited.chunk.page_number,
                    source=cited.chunk.source,
                )
            )
        return resolved
