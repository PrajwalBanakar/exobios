import time

import openai
from openai import OpenAI

from app.generation.exceptions import (
    EmptyModelResponseError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRefusalError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    StructuredOutputError,
)
from app.generation.models.request import GenerationRequest
from app.generation.models.response import ClinicalGenerationDraft, RawGenerationResponse
from app.generation.models.usage import TokenUsage
from app.generation.providers.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """Generates structured clinical drafts via OpenAI's Responses API
    (`client.responses.parse(text_format=...)`), the SDK's current
    structured-output mechanism (openai-python 1.109, inspected before
    writing this). This deliberately does *not* use the older
    `chat.completions.parse(response_format=...)` path: that helper raises
    `LengthFinishReasonError`/`ContentFilterFinishReasonError` for
    truncation and content-filtering, which collapses the
    refusal/empty/malformed distinctions this provider is required to
    handle explicitly. The Responses API instead surfaces those as
    inspectable response state (`status`, a `refusal` content item,
    `output_parsed`), which is what `_extract_draft` reads.

    No OpenAI SDK type crosses this module's boundary — every public method
    takes and returns project-owned models (GenerationRequest,
    RawGenerationResponse), and every `openai.*` exception is mapped to a
    project exception before it can propagate.
    """

    def __init__(
        self,
        client: OpenAI,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.2,
        max_output_tokens: int = 1500,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._client = client
        self._model = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._timeout_seconds = timeout_seconds

    def generate_structured(self, request: GenerationRequest) -> RawGenerationResponse:
        model = request.model or self._model
        params = request.parameters
        temperature = params.temperature if params.temperature is not None else self._temperature
        max_output_tokens = (
            params.max_output_tokens
            if params.max_output_tokens is not None
            else self._max_output_tokens
        )
        timeout_seconds = (
            params.timeout_seconds if params.timeout_seconds is not None else self._timeout_seconds
        )

        start = time.perf_counter()
        try:
            response = self._client.responses.parse(
                model=model,
                input=request.prompt_response.prompt,
                text_format=ClinicalGenerationDraft,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                timeout=timeout_seconds,
            )
        except openai.AuthenticationError as exc:
            raise ProviderAuthenticationError(reason=str(exc)) from exc
        except openai.RateLimitError as exc:
            raise ProviderRateLimitError(reason=str(exc)) from exc
        except openai.APITimeoutError as exc:
            raise ProviderTimeoutError(reason=str(exc)) from exc
        except openai.APIError as exc:
            raise ProviderUnavailableError(reason=str(exc)) from exc
        except Exception as exc:
            raise ProviderUnavailableError(reason=str(exc)) from exc
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        draft = self._extract_draft(response)
        usage = self._extract_usage(response)

        return RawGenerationResponse(
            draft=draft,
            model=response.model or model,
            usage=usage,
            finish_reason=self._finish_reason(response),
            provider_request_id=getattr(response, "_request_id", None),
            latency_ms=latency_ms,
        )

    def _extract_draft(self, response) -> ClinicalGenerationDraft:
        # Refusal is checked before emptiness/malformedness: a refusal
        # response still has `output` items (a message containing a
        # `refusal` content part), so checking `output_parsed is None`
        # first would misclassify it as "empty" or "malformed" instead of
        # the more specific, more actionable refusal case.
        for item in response.output or []:
            if getattr(item, "type", None) != "message":
                continue
            for content in item.content:
                if getattr(content, "type", None) == "refusal":
                    raise ProviderRefusalError(reason=content.refusal)

        parsed = response.output_parsed
        if parsed is None:
            if not response.output:
                raise EmptyModelResponseError(reason="Provider returned no output items")
            raise StructuredOutputError(
                reason=f"Provider response did not match the expected schema "
                f"(status={response.status})"
            )
        return parsed

    def _extract_usage(self, response) -> TokenUsage:
        usage = response.usage
        if usage is None:
            return TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0)
        return TokenUsage(
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
        )

    def _finish_reason(self, response) -> str:
        if response.status == "incomplete" and response.incomplete_details is not None:
            return f"incomplete:{response.incomplete_details.reason}"
        return response.status or "unknown"

    def health(self) -> bool:
        # Deliberately no network call: constructing this provider already
        # requires a client bound to a (non-blank, validated) API key, so
        # "healthy" here means "usable", not "OpenAI is currently
        # reachable." A liveness probe hitting client.models.list() on
        # every health check would burn quota/latency for no benefit here;
        # a deeper check is a reasonable future addition (see deliverables).
        return self._client is not None
