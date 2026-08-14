import json
import logging

import groq
from groq import Groq
from pydantic import BaseModel

from config.settings import settings
from core.exceptions import LLMGenerationException
from core.retry import retry_with_backoff

logger = logging.getLogger("app.llm")

_RETRYABLE_GROQ_ERRORS = (groq.APIConnectionError, groq.APITimeoutError, groq.RateLimitError, groq.InternalServerError)


class LLMService:
    """Wraps Groq with forced JSON output matching a given Pydantic schema."""

    def __init__(self):
        # Explicit request timeout — without it a hung Groq call could tie up
        # a worker thread indefinitely, since /analyze has no outer deadline.
        self.client = Groq(api_key=settings.llm.groq_api_key, timeout=60.0)
        self.model = settings.llm.model

    def generate_structured(self, system_prompt: str, user_prompt: str, response_schema: type[BaseModel]) -> BaseModel:
        # Build strict system prompt forcing JSON schema adherence
        full_system_prompt = (
            f"{system_prompt}\n\n"
            "CRITICAL REQUIREMENT: You MUST respond strictly with valid JSON. "
            "Your output must adhere to this JSON Schema:\n"
            f"{json.dumps(response_schema.model_json_schema())}"
        )

        def _call():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": full_system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=settings.llm.max_output_tokens,
                temperature=settings.llm.temperature,
            )
            return response.choices[0].message.content

        try:
            raw = retry_with_backoff(
                _call,
                is_retryable=lambda e: isinstance(e, _RETRYABLE_GROQ_ERRORS),
                op_name="groq call",
            )
        except Exception as e:
            raise LLMGenerationException(f"groq call failed: {e}") from e

        try:
            return response_schema.model_validate_json(raw)
        except Exception as e:
            logger.error(f"schema validation failed on raw output: {raw[:500] if raw else 'None'}")
            raise LLMGenerationException(f"llm output failed schema validation: {e}") from e


llm_service = LLMService()