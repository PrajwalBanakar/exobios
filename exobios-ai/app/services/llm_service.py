import json
import logging

from groq import Groq
from pydantic import BaseModel

from config.settings import settings
from core.exceptions import LLMGenerationException

logger = logging.getLogger("app.llm")


class LLMService:
    """Wraps Groq with forced JSON output matching a given Pydantic schema."""

    def __init__(self):
        self.client = Groq(api_key=settings.llm.groq_api_key)
        self.model = settings.llm.model

    def generate_structured(self, system_prompt: str, user_prompt: str, response_schema: type[BaseModel]) -> BaseModel:
        # Build strict system prompt forcing JSON schema adherence
        full_system_prompt = (
            f"{system_prompt}\n\n"
            "CRITICAL REQUIREMENT: You MUST respond strictly with valid JSON. "
            "Your output must adhere to this JSON Schema:\n"
            f"{json.dumps(response_schema.model_json_schema())}"
        )

        try:
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
            raw = response.choices[0].message.content
        except Exception as e:
            raise LLMGenerationException(f"groq call failed: {e}")

        try:
            return response_schema.model_validate_json(raw)
        except Exception as e:
            logger.error(f"schema validation failed on raw output: {raw[:500] if raw else 'None'}")
            raise LLMGenerationException(f"llm output failed schema validation: {e}")


llm_service = LLMService()