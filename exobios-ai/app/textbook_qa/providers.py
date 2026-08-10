import time
from abc import ABC, abstractmethod

import openai
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

from app.generation.exceptions import (
    EmptyModelResponseError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRefusalError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    StructuredOutputError,
)
from app.generation.models.usage import TokenUsage
from app.textbook_qa.models import TextbookAnswerDraft

# These providers exist because GenerationRequest/RawGenerationResponse/
# LLMProvider (app.generation) hard-code ClinicalGenerationDraft as the
# structured-output schema — there is no parameter to swap it for
# TextbookAnswerDraft. Rather than a generics refactor of the existing,
# tested clinical generation pipeline (real risk to the working IMNCI demo,
# for a deadline-pressured phase), this is a small, deliberately parallel
# set of provider callers targeting a different schema. Every exception
# type and the overall call shape is reused as-is from app.generation.


class TextbookRawResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft: TextbookAnswerDraft
    model: str
    usage: TokenUsage
    finish_reason: str
    latency_ms: float = Field(ge=0)


class TextbookLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> TextbookRawResponse: ...

    @abstractmethod
    def health(self) -> bool: ...


class OpenAITextbookProvider(TextbookLLMProvider):
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

    def generate(self, prompt: str) -> TextbookRawResponse:
        start = time.perf_counter()
        try:
            response = self._client.responses.parse(
                model=self._model,
                input=prompt,
                text_format=TextbookAnswerDraft,
                temperature=self._temperature,
                max_output_tokens=self._max_output_tokens,
                timeout=self._timeout_seconds,
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
        return TextbookRawResponse(
            draft=draft,
            model=response.model or self._model,
            usage=usage,
            finish_reason=self._finish_reason(response),
            latency_ms=latency_ms,
        )

    def _extract_draft(self, response) -> TextbookAnswerDraft:
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
        return self._client is not None


def _strip_additional_properties(node: object) -> None:
    if isinstance(node, dict):
        node.pop("additionalProperties", None)
        for value in node.values():
            _strip_additional_properties(value)
    elif isinstance(node, list):
        for item in node:
            _strip_additional_properties(item)


def _response_schema() -> dict:
    schema = TextbookAnswerDraft.model_json_schema()
    _strip_additional_properties(schema)
    return schema


class GeminiTextbookProvider(TextbookLLMProvider):
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

    def generate(self, prompt: str) -> TextbookRawResponse:
        start = time.perf_counter()
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self._temperature,
                    max_output_tokens=self._max_output_tokens,
                    response_mime_type="application/json",
                    response_schema=_response_schema(),
                    http_options=types.HttpOptions(timeout=int(self._timeout_seconds * 1000)),
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
        return TextbookRawResponse(
            draft=draft,
            model=self._model,
            usage=usage,
            finish_reason=self._finish_reason(response),
            latency_ms=latency_ms,
        )

    def _extract_draft(self, response) -> TextbookAnswerDraft:
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
        if isinstance(parsed, TextbookAnswerDraft):
            return parsed
        return TextbookAnswerDraft.model_validate(parsed)

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
        return self._client is not None
