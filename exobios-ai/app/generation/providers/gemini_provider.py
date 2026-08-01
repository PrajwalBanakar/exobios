import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.generation.exceptions import (
    EmptyModelResponseError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRefusalError,
    ProviderUnavailableError,
    StructuredOutputError,
)
from app.generation.models.request import GenerationRequest
from app.generation.models.response import ClinicalGenerationDraft, RawGenerationResponse
from app.generation.models.usage import TokenUsage
from app.generation.providers.base import LLMProvider


def _strip_additional_properties(node: object) -> None:
    """Recursively deletes 'additionalProperties' from a JSON schema dict.

    Pydantic's `model_json_schema()` emits `"additionalProperties": false` on
    every `extra="forbid"` model (all of ours). Gemini's Schema type has a
    field for it, so unlike unsupported keywords such as `minLength` (which
    google-genai's Schema.model_validate silently drops), a literal
    `additionalProperties` survives into the request and the Gemini API
    rejects it outright — this must be removed before the schema is handed
    to the SDK, not just left for the SDK's (version-dependent, observed to
    not always fire) local validation to catch.
    """
    if isinstance(node, dict):
        node.pop("additionalProperties", None)
        for value in node.values():
            _strip_additional_properties(value)
    elif isinstance(node, list):
        for item in node:
            _strip_additional_properties(item)


def _response_schema() -> dict:
    schema = ClinicalGenerationDraft.model_json_schema()
    _strip_additional_properties(schema)
    return schema


class GeminiProvider(LLMProvider):
    """Generates structured clinical drafts via the Gemini API. Free-tier
    alternative to OpenAIProvider for local dev/demo use — implements the
    same LLMProvider interface via Gemini's native structured-output support
    (`response_schema` bound to the same ClinicalGenerationDraft Pydantic
    model OpenAIProvider uses), so GenerationService and ResponseValidator
    are unchanged.

    No google-genai SDK type crosses this module's boundary — every public
    method takes and returns project-owned models (GenerationRequest,
    RawGenerationResponse), and every google.genai exception is mapped to a
    project exception before it can propagate.
    """

    def __init__(
        self,
        client: genai.Client,
        model: str = "gemini-flash-latest",
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
            response = self._client.models.generate_content(
                model=model,
                contents=request.prompt_response.prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                    response_mime_type="application/json",
                    response_schema=_response_schema(),
                    http_options=types.HttpOptions(timeout=int(timeout_seconds * 1000)),
                ),
            )
        except genai_errors.ClientError as exc:
            if exc.code in (401, 403):
                raise ProviderAuthenticationError(reason=str(exc)) from exc
            if exc.code == 429:
                raise ProviderRateLimitError(reason=str(exc)) from exc
            raise ProviderUnavailableError(reason=str(exc)) from exc
        except genai_errors.ServerError as exc:
            raise ProviderUnavailableError(reason=str(exc)) from exc
        except Exception as exc:
            raise ProviderUnavailableError(reason=str(exc)) from exc
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        draft = self._extract_draft(response)
        usage = self._extract_usage(response)

        return RawGenerationResponse(
            draft=draft,
            model=model,
            usage=usage,
            finish_reason=self._finish_reason(response),
            provider_request_id=None,
            latency_ms=latency_ms,
        )

    def _extract_draft(self, response) -> ClinicalGenerationDraft:
        # Blocked-prompt and per-candidate safety refusals are both surfaced
        # as ProviderRefusalError, mirroring OpenAIProvider treating a
        # content-policy refusal as a distinct, well-formed outcome rather
        # than a transport failure.
        feedback = response.prompt_feedback
        if feedback is not None and feedback.block_reason is not None:
            raise ProviderRefusalError(reason=str(feedback.block_reason))

        candidates = response.candidates or []
        if not candidates:
            raise EmptyModelResponseError(reason="Provider returned no candidates")

        if candidates[0].finish_reason == types.FinishReason.SAFETY:
            raise ProviderRefusalError(reason="Response blocked by safety filters")

        parsed = response.parsed
        if parsed is None:
            if not response.text:
                raise EmptyModelResponseError(reason="Provider returned no output text")
            raise StructuredOutputError(
                reason=f"Provider response did not match the expected schema "
                f"(finish_reason={candidates[0].finish_reason})"
            )
        if isinstance(parsed, ClinicalGenerationDraft):
            return parsed
        return ClinicalGenerationDraft.model_validate(parsed)

    def _extract_usage(self, response) -> TokenUsage:
        usage = response.usage_metadata
        if usage is None:
            return TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0)
        return TokenUsage(
            input_tokens=usage.prompt_token_count or 0,
            output_tokens=usage.candidates_token_count or 0,
            total_tokens=usage.total_token_count or 0,
        )

    def _finish_reason(self, response) -> str:
        candidates = response.candidates or []
        if not candidates or candidates[0].finish_reason is None:
            return "unknown"
        return str(candidates[0].finish_reason)

    def health(self) -> bool:
        # Deliberately no network call — see OpenAIProvider.health for the
        # same rationale: constructing this provider already requires a
        # client bound to a (non-blank) API key.
        return self._client is not None
