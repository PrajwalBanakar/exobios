import pytest

from app.generation.models.usage import TokenUsage
from app.prompting.formatting.context_formatter import ContextFormatter
from app.retrieval.models.retrieval import SearchResponse
from app.textbook_qa.exceptions import TextbookAnswerValidationError, UnsupportedGroundingModeError
from app.textbook_qa.models import GroundingMode, TextbookAnswerDraft, TextbookQuestionRequest
from app.textbook_qa.prompt_builder import TextbookPromptBuilder
from app.textbook_qa.providers import TextbookRawResponse
from app.textbook_qa.service import TextbookQAService
from app.textbook_qa.validator import TextbookAnswerValidator


class FakeRetrievalService:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def search(self, request):
        self.calls.append(request)
        return SearchResponse(
            query=request.query,
            results=self.results,
            result_count=len(self.results),
            elapsed_ms=1.0,
        )


class FakeTextbookProvider:
    def __init__(self, draft, model="fake-model", fail_with=None):
        self.draft = draft
        self.model = model
        self.fail_with = fail_with
        self.calls = []

    def generate(self, prompt):
        self.calls.append(prompt)
        if self.fail_with is not None:
            raise self.fail_with
        return TextbookRawResponse(
            draft=self.draft,
            model=self.model,
            usage=TokenUsage(input_tokens=1, output_tokens=1, total_tokens=2),
            finish_reason="stop",
            latency_ms=10.0,
        )

    def health(self) -> bool:
        return True


def _service(retrieval_service, provider, *, min_retrieval_score=0.5, mode=GroundingMode.STRICT):
    return TextbookQAService(
        retrieval_service=retrieval_service,
        prompt_builder=TextbookPromptBuilder(context_formatter=ContextFormatter()),
        provider=provider,
        validator=TextbookAnswerValidator(),
        grounding_mode=mode,
        min_retrieval_score=min_retrieval_score,
    )


def test_retrieval_level_refusal_when_no_results():
    retrieval_service = FakeRetrievalService(results=[])
    provider = FakeTextbookProvider(draft=None)
    service = _service(retrieval_service, provider)

    result = service.answer(TextbookQuestionRequest(question="What is the weather today?"))

    assert result.status.value == "INSUFFICIENT_EVIDENCE"
    assert result.refusal_stage == "retrieval"
    assert provider.calls == []


def test_retrieval_level_refusal_when_top_score_below_threshold(textbook_chunk_factory):
    weak_chunk = textbook_chunk_factory(score=0.2)
    retrieval_service = FakeRetrievalService(results=[weak_chunk])
    provider = FakeTextbookProvider(draft=None)
    service = _service(retrieval_service, provider, min_retrieval_score=0.5)

    result = service.answer(TextbookQuestionRequest(question="Unrelated question"))

    assert result.status.value == "INSUFFICIENT_EVIDENCE"
    assert result.refusal_stage == "retrieval"
    assert result.top_score == 0.2
    assert provider.calls == []


def test_generation_level_refusal_when_model_reports_insufficient_evidence(textbook_chunk_factory):
    chunk = textbook_chunk_factory(score=0.9)
    retrieval_service = FakeRetrievalService(results=[chunk])
    draft = TextbookAnswerDraft(
        insufficient_evidence=True, answer="Not enough information to answer.", citations=[]
    )
    provider = FakeTextbookProvider(draft=draft)
    service = _service(retrieval_service, provider, min_retrieval_score=0.5)

    result = service.answer(TextbookQuestionRequest(question="q"))

    assert result.status.value == "INSUFFICIENT_EVIDENCE"
    assert result.refusal_stage == "generation"
    assert len(provider.calls) == 1


def test_successful_answer_resolves_citations(textbook_chunk_factory):
    chunk = textbook_chunk_factory(score=0.9)
    retrieval_service = FakeRetrievalService(results=[chunk])
    draft = TextbookAnswerDraft(
        insufficient_evidence=False, answer="The cardiac cycle has phases [S1].", citations=[1]
    )
    provider = FakeTextbookProvider(draft=draft, model="gpt-4.1-mini")
    service = _service(retrieval_service, provider, min_retrieval_score=0.5)

    result = service.answer(TextbookQuestionRequest(question="Explain the cardiac cycle"))

    assert result.status.value == "ANSWERED"
    assert result.answer == "The cardiac cycle has phases [S1]."
    assert len(result.citations) == 1
    assert result.citations[0].chapter_number == "9"
    assert result.model == "gpt-4.1-mini"


def test_invalid_citation_raises_validation_error(textbook_chunk_factory):
    chunk = textbook_chunk_factory(score=0.9)
    retrieval_service = FakeRetrievalService(results=[chunk])
    draft = TextbookAnswerDraft(insufficient_evidence=False, answer="Answer [S99].", citations=[99])
    provider = FakeTextbookProvider(draft=draft)
    service = _service(retrieval_service, provider, min_retrieval_score=0.5)

    with pytest.raises(TextbookAnswerValidationError):
        service.answer(TextbookQuestionRequest(question="q"))


def test_unsupported_grounding_mode_raises_before_any_retrieval(textbook_chunk_factory):
    retrieval_service = FakeRetrievalService(results=[textbook_chunk_factory()])
    provider = FakeTextbookProvider(draft=None)
    service = _service(retrieval_service, provider, mode=GroundingMode.AUGMENTED)

    with pytest.raises(UnsupportedGroundingModeError):
        service.answer(TextbookQuestionRequest(question="q"))

    assert retrieval_service.calls == []


def test_subject_and_document_id_forwarded_to_retrieval(textbook_chunk_factory):
    from app.ingestion.models.document import Subject

    chunk = textbook_chunk_factory(score=0.9)
    retrieval_service = FakeRetrievalService(results=[chunk])
    draft = TextbookAnswerDraft(insufficient_evidence=False, answer="Answer [S1].", citations=[1])
    provider = FakeTextbookProvider(draft=draft)
    service = _service(retrieval_service, provider, min_retrieval_score=0.5)

    service.answer(TextbookQuestionRequest(question="q", subject=Subject.PHYSIOLOGY))

    assert retrieval_service.calls[0].subject == Subject.PHYSIOLOGY
