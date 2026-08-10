import logging
import time
from uuid import uuid4

from app.retrieval.exceptions import RetrievalError, SearchError
from app.retrieval.models.retrieval import SearchRequest, SearchResponse
from app.retrieval.services.retrieval_service import RetrievalService
from app.textbook_qa.exceptions import TextbookAnswerValidationError, UnsupportedGroundingModeError
from app.textbook_qa.models import (
    GroundingMode,
    TextbookAnswerResult,
    TextbookAnswerStatus,
    TextbookQuestionRequest,
)
from app.textbook_qa.prompt_builder import TextbookPromptBuilder
from app.textbook_qa.providers import TextbookLLMProvider
from app.textbook_qa.validator import TextbookAnswerValidator

logger = logging.getLogger("app.textbook_qa")


class TextbookQAService:
    """Orchestrates: retrieve (subject/document_id-filtered) -> evidence
    threshold check (retrieval-level refusal) -> build strict-grounding
    prompt -> LLM call -> generation-level refusal check -> citation
    validation/resolution -> TextbookAnswerResult.

    Two independent refusal points (PART 15): a weak top retrieval score
    never reaches the LLM at all; a model that says insufficient_evidence
    after seeing real evidence is trusted and returned as a refusal too. In
    neither case does citation-looking text alone count as "grounded" —
    TextbookAnswerValidator must resolve every citation number against the
    trusted retrieved context first.
    """

    def __init__(
        self,
        retrieval_service: RetrievalService,
        prompt_builder: TextbookPromptBuilder,
        provider: TextbookLLMProvider,
        validator: TextbookAnswerValidator,
        grounding_mode: GroundingMode,
        min_retrieval_score: float,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._prompt_builder = prompt_builder
        self._provider = provider
        self._validator = validator
        self._grounding_mode = grounding_mode
        self._min_retrieval_score = min_retrieval_score

    def answer(self, request: TextbookQuestionRequest) -> TextbookAnswerResult:
        if self._grounding_mode is not GroundingMode.STRICT:
            raise UnsupportedGroundingModeError(mode=self._grounding_mode.value)

        request_id = str(uuid4())
        logger.info(
            "textbook_qa_started request_id=%s subject=%s document_id=%s",
            request_id,
            request.subject,
            request.document_id,
        )

        search_response = self._retrieve(request, request_id)
        top_score = max((chunk.score for chunk in search_response.results), default=None)

        if (
            not search_response.results
            or top_score is None
            or top_score < self._min_retrieval_score
        ):
            logger.info(
                "textbook_qa_insufficient_evidence request_id=%s stage=retrieval "
                "chunk_count=%s top_score=%s threshold=%s",
                request_id,
                len(search_response.results),
                top_score,
                self._min_retrieval_score,
            )
            return TextbookAnswerResult(
                request_id=request_id,
                status=TextbookAnswerStatus.INSUFFICIENT_EVIDENCE,
                retrieved_chunk_count=len(search_response.results),
                top_score=top_score,
                refusal_stage="retrieval",
            )

        prompt, retrieved_context = self._prompt_builder.build(
            request.question, search_response.results, self._grounding_mode
        )

        start = time.perf_counter()
        raw = self._provider.generate(prompt)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "textbook_qa_generation_completed request_id=%s model=%s finish_reason=%s "
            "insufficient_evidence=%s latency_ms=%s",
            request_id,
            raw.model,
            raw.finish_reason,
            raw.draft.insufficient_evidence,
            latency_ms,
        )

        if raw.draft.insufficient_evidence:
            return TextbookAnswerResult(
                request_id=request_id,
                status=TextbookAnswerStatus.INSUFFICIENT_EVIDENCE,
                retrieved_chunk_count=len(search_response.results),
                top_score=top_score,
                refusal_stage="generation",
                model=raw.model,
                latency_ms=latency_ms,
            )

        try:
            citations = self._validator.validate_and_resolve(raw.draft, retrieved_context)
        except TextbookAnswerValidationError:
            logger.error("textbook_qa_validation_failed request_id=%s", request_id)
            raise

        logger.info(
            "textbook_qa_completed request_id=%s citation_count=%s", request_id, len(citations)
        )
        return TextbookAnswerResult(
            request_id=request_id,
            status=TextbookAnswerStatus.ANSWERED,
            answer=raw.draft.answer,
            citations=citations,
            retrieved_chunk_count=len(search_response.results),
            top_score=top_score,
            model=raw.model,
            latency_ms=latency_ms,
        )

    def _retrieve(self, request: TextbookQuestionRequest, request_id: str) -> SearchResponse:
        search_request = SearchRequest(
            query=request.question,
            subject=request.subject,
            document_id=request.document_id,
            top_k=request.top_k,
            max_returned_chunks=request.max_returned_chunks,
        )
        try:
            return self._retrieval_service.search(search_request)
        except (RetrievalError, SearchError):
            logger.error("textbook_qa_failed request_id=%s stage=retrieval", request_id)
            raise
