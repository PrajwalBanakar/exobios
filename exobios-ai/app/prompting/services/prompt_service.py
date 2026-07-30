import logging
import time
from uuid import UUID

from app.embeddings.exceptions import EmbeddingGenerationError
from app.prompting.builders.base import PromptBuilder
from app.prompting.exceptions import ContextFormattingError, PromptBuildError
from app.prompting.formatting.context_formatter import ContextFormatter
from app.prompting.models.prompt import (
    PromptContext,
    PromptRequest,
    PromptResponse,
    PromptTemplateName,
    RetrievedContext,
)
from app.retrieval.exceptions import RetrievalError, SearchError
from app.retrieval.models.retrieval import RetrievedChunk, SearchResponse
from app.retrieval.services.retrieval_service import RetrievalService

logger = logging.getLogger("app.prompting")


class PromptService:
    """Orchestrates: retrieve context -> format context -> assemble prompt.

    Depends only on RetrievalService (the system's retrieval capability —
    embedding the query and searching the vector store are already fully
    encapsulated there, so this layer stays provider-agnostic), PromptBuilder,
    and ContextFormatter. Never calls an LLM; the output is a PromptResponse
    ready to be sent to one.
    """

    def __init__(
        self,
        retrieval_service: RetrievalService,
        prompt_builder: PromptBuilder,
        context_formatter: ContextFormatter,
        default_template: PromptTemplateName = PromptTemplateName.DIAGNOSIS,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._prompt_builder = prompt_builder
        self._context_formatter = context_formatter
        self._default_template = default_template

    def build_prompt(self, request: PromptRequest) -> PromptResponse:
        start = time.perf_counter()
        assessment_id = request.patient.assessment_id
        template = request.template or self._default_template

        logger.info("prompt_started assessment_id=%s template=%s", assessment_id, template)

        search_response = self._retrieve(assessment_id, request)
        retrieved_context = self._format(assessment_id, search_response.results)

        prompt_context = PromptContext(patient=request.patient, retrieved_context=retrieved_context)
        response = self._build(assessment_id, prompt_context, template)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "prompt_completed assessment_id=%s prompt_tokens=%s context_tokens=%s "
            "chunk_count=%s discarded_chunks=%s elapsed_time=%s",
            assessment_id,
            response.statistics.prompt_tokens,
            response.statistics.context_tokens,
            response.statistics.included_chunk_count,
            response.statistics.discarded_chunk_count,
            elapsed_ms,
        )
        return response

    def _retrieve(self, assessment_id: UUID, request: PromptRequest) -> SearchResponse:
        try:
            search_response = self._retrieval_service.search(request.search_request)
        except (RetrievalError, SearchError, EmbeddingGenerationError):
            logger.error("prompt_failed assessment_id=%s stage=retrieval", assessment_id)
            raise
        except Exception as exc:
            logger.error("prompt_failed assessment_id=%s stage=retrieval", assessment_id)
            raise PromptBuildError(reason=str(exc)) from exc

        logger.info(
            "context_retrieved assessment_id=%s chunk_count=%s",
            assessment_id,
            search_response.result_count,
        )
        return search_response

    def _format(self, assessment_id: UUID, chunks: list[RetrievedChunk]) -> RetrievedContext:
        try:
            retrieved_context = self._context_formatter.format(chunks)
        except ContextFormattingError:
            logger.error("prompt_failed assessment_id=%s stage=formatting", assessment_id)
            raise
        except Exception as exc:
            logger.error("prompt_failed assessment_id=%s stage=formatting", assessment_id)
            raise ContextFormattingError(reason=str(exc)) from exc

        logger.info(
            "context_formatted assessment_id=%s chunk_count=%s",
            assessment_id,
            retrieved_context.total_chunks,
        )
        return retrieved_context

    def _build(
        self, assessment_id: UUID, prompt_context: PromptContext, template: PromptTemplateName
    ) -> PromptResponse:
        try:
            response = self._prompt_builder.build(prompt_context, template)
        except PromptBuildError:
            logger.error("prompt_failed assessment_id=%s stage=building", assessment_id)
            raise
        except Exception as exc:
            logger.error("prompt_failed assessment_id=%s stage=building", assessment_id)
            raise PromptBuildError(reason=str(exc)) from exc

        logger.info(
            "prompt_built assessment_id=%s prompt_tokens=%s section_count=%s",
            assessment_id,
            response.statistics.prompt_tokens,
            len(response.sections),
        )
        return response
