import logging
import time
from datetime import UTC, datetime

from app.generation.exceptions import (
    GenerationError,
    GenerationValidationError,
    PromptBudgetExceededError,
    ProviderUnavailableError,
)
from app.generation.models.request import GenerationRequest
from app.generation.models.response import (
    ClinicalGenerationOutput,
    GenerationMetadata,
    GenerationResult,
    RawGenerationResponse,
)
from app.generation.providers.base import LLMProvider
from app.generation.validation.response_validator import ResponseValidator

logger = logging.getLogger("app.generation")


class GenerationService:
    """Orchestrates: validate prompt is usable -> call LLMProvider ->
    validate and resolve the structured output -> GenerationResult.

    Depends only on LLMProvider and ResponseValidator interfaces — never on
    OpenAI or any other provider SDK directly. Consumes an already-completed
    PromptResponse (AI-5's output); never calls RetrievalService or
    PromptService itself.

    Never logs patient complaint/symptom text, the full prompt, retrieved
    chunks, or raw model output — only operational metadata (see each log
    call below).
    """

    def __init__(
        self,
        provider: LLMProvider,
        validator: ResponseValidator,
        context_window_tokens: int | None = None,
    ) -> None:
        self._provider = provider
        self._validator = validator
        self._context_window_tokens = context_window_tokens

    def generate(self, request: GenerationRequest) -> GenerationResult:
        start = time.perf_counter()
        prompt_response = request.prompt_response
        logger.info(
            "generation_started request_id=%s model=%s template=%s prompt_token_estimate=%s",
            request.request_id,
            request.model or "-",
            prompt_response.metadata.template,
            prompt_response.statistics.prompt_tokens,
        )

        self._validate_prompt_usable(request)
        self._validate_token_budget(request)

        raw = self._call_provider(request)
        output = self._validate_output(request, raw)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "generation_completed request_id=%s model=%s input_tokens=%s output_tokens=%s "
            "total_tokens=%s finish_reason=%s citation_count=%s condition_count=%s "
            "red_flag_count=%s elapsed_time=%s",
            request.request_id,
            raw.model,
            raw.usage.input_tokens,
            raw.usage.output_tokens,
            raw.usage.total_tokens,
            raw.finish_reason,
            len(output.citations),
            len(output.possible_conditions),
            len(output.red_flags),
            elapsed_ms,
        )

        return GenerationResult(
            request_id=request.request_id,
            output=output,
            resolved_citations=output.citations,
            metadata=GenerationMetadata(
                model=raw.model,
                usage=raw.usage,
                latency_ms=raw.latency_ms,
                finish_reason=raw.finish_reason,
                provider_request_id=raw.provider_request_id,
                generated_at=datetime.now(UTC),
            ),
        )

    def _validate_prompt_usable(self, request: GenerationRequest) -> None:
        if not request.prompt_response.prompt.strip():
            logger.error(
                "generation_failed request_id=%s stage=prompt_validation", request.request_id
            )
            raise GenerationValidationError(reason="prompt is blank")

    def _validate_token_budget(self, request: GenerationRequest) -> None:
        if self._context_window_tokens is None:
            return

        stats = request.prompt_response.statistics
        required = stats.prompt_tokens + stats.reserved_response_tokens
        if required > self._context_window_tokens:
            logger.error("generation_failed request_id=%s stage=budget_check", request.request_id)
            raise PromptBudgetExceededError(
                reason=(
                    f"prompt_tokens ({stats.prompt_tokens}) + reserved_response_tokens "
                    f"({stats.reserved_response_tokens}) = {required} exceeds the configured "
                    f"context window of {self._context_window_tokens} tokens"
                )
            )

    def _call_provider(self, request: GenerationRequest) -> RawGenerationResponse:
        logger.info(
            "provider_request_started request_id=%s model=%s",
            request.request_id,
            request.model or "-",
        )
        try:
            raw = self._provider.generate_structured(request)
        except GenerationError:
            logger.error("provider_request_failed request_id=%s", request.request_id)
            logger.error("generation_failed request_id=%s stage=provider", request.request_id)
            raise
        except Exception as exc:
            logger.error("provider_request_failed request_id=%s", request.request_id)
            logger.error("generation_failed request_id=%s stage=provider", request.request_id)
            raise ProviderUnavailableError(reason=str(exc)) from exc

        logger.info(
            "provider_request_completed request_id=%s model=%s finish_reason=%s "
            "input_tokens=%s output_tokens=%s total_tokens=%s",
            request.request_id,
            raw.model,
            raw.finish_reason,
            raw.usage.input_tokens,
            raw.usage.output_tokens,
            raw.usage.total_tokens,
        )
        return raw

    def _validate_output(
        self, request: GenerationRequest, raw: RawGenerationResponse
    ) -> ClinicalGenerationOutput:
        logger.info("generation_validation_started request_id=%s", request.request_id)
        try:
            output = self._validator.validate_and_resolve(
                raw.draft, request.prompt_response.retrieved_context
            )
        except GenerationValidationError:
            logger.error("generation_validation_failed request_id=%s", request.request_id)
            logger.error("generation_failed request_id=%s stage=validation", request.request_id)
            raise
        except Exception as exc:
            logger.error("generation_validation_failed request_id=%s", request.request_id)
            logger.error("generation_failed request_id=%s stage=validation", request.request_id)
            raise GenerationValidationError(reason=str(exc)) from exc

        logger.info(
            "generation_validation_completed request_id=%s citation_count=%s "
            "condition_count=%s red_flag_count=%s",
            request.request_id,
            len(output.citations),
            len(output.possible_conditions),
            len(output.red_flags),
        )
        return output
