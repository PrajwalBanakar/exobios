from app.prompting.models.prompt import CitedChunk, RetrievedContext
from app.textbook_qa.exceptions import TextbookAnswerValidationError
from app.textbook_qa.models import TextbookAnswerDraft, TextbookCitation


class TextbookAnswerValidator:
    """Deterministic, Python-only validation of a TextbookAnswerDraft
    against the trusted RetrievedContext it was generated from — mirrors
    app.generation.validation.ResponseValidator's pattern exactly (never
    trust the model beyond citation *numbers*; resolve everything else from
    the retrieved context; reject outright on an unknown citation rather
    than silently dropping it, since that could mask an invented source).
    """

    def validate_and_resolve(
        self, draft: TextbookAnswerDraft, context: RetrievedContext
    ) -> list[TextbookCitation]:
        try:
            return self._validate_and_resolve(draft, context)
        except TextbookAnswerValidationError:
            raise
        except Exception as exc:
            raise TextbookAnswerValidationError(reason=str(exc)) from exc

    def _validate_and_resolve(
        self, draft: TextbookAnswerDraft, context: RetrievedContext
    ) -> list[TextbookCitation]:
        if not draft.answer.strip():
            raise TextbookAnswerValidationError(reason="answer must not be blank")

        index = self._build_citation_index(context)
        invalid = set(draft.citations) - index.keys()
        if invalid:
            raise TextbookAnswerValidationError(
                reason=f"response cited unknown citation numbers: {sorted(invalid)}"
            )

        if not draft.citations:
            # A non-refusal answer with zero citations isn't grounded — the
            # prompt requires every substantive claim to carry a marker, so
            # an empty citations list means either a trivial non-answer or
            # the model silently dropping the requirement. Fail safe rather
            # than surface an ungrounded answer as if it were sourced.
            raise TextbookAnswerValidationError(
                reason="non-refusal answer must cite at least one source"
            )

        return self._resolve_citations(draft.citations, index)

    def _build_citation_index(self, context: RetrievedContext) -> dict[int, CitedChunk]:
        return {
            cited.citation_number: cited for group in context.groups for cited in group.citations
        }

    def _resolve_citations(
        self, citation_numbers: list[int], index: dict[int, CitedChunk]
    ) -> list[TextbookCitation]:
        resolved: list[TextbookCitation] = []
        seen: set[int] = set()
        for number in citation_numbers:
            if number in seen:
                continue
            seen.add(number)
            chunk = index[number].chunk
            resolved.append(
                TextbookCitation(
                    citation_number=number,
                    document_id=chunk.document_id,
                    title=chunk.title,
                    subject=chunk.subject,
                    edition=chunk.edition,
                    chapter_number=chunk.chapter_number,
                    chapter_title=chunk.chapter_title,
                    section_title=chunk.section_title,
                    pdf_page_start=chunk.pdf_page_start,
                    pdf_page_end=chunk.pdf_page_end,
                    printed_page_start=chunk.printed_page_start,
                    printed_page_end=chunk.printed_page_end,
                )
            )
        return resolved
