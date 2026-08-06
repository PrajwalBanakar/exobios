import json
import logging

from google import genai
from google.genai import types
from pydantic import BaseModel

from config.settings import settings
from core.exceptions import LLMGenerationException

logger = logging.getLogger("app.llm")


class LLMService:
    """Wraps Gemini with forced JSON output matching a given Pydantic schema.
    No API key/billing card needed for Gemini's free tier, per the decision
    to avoid OpenAI's billing requirement."""

    def __init__(self):
        self.client = genai.Client(api_key=settings.llm.gemini_api_key)
        self.model = settings.llm.model

    def generate_structured(self, system_prompt: str, user_prompt: str, response_schema: type[BaseModel]) -> BaseModel:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    max_output_tokens=settings.llm.max_output_tokens,
                    temperature=settings.llm.temperature,
                ),
            )
            raw = response.text
        except Exception as e:
            raise LLMGenerationException(f"gemini call failed: {e}")

        try:
            return response_schema.model_validate_json(raw)
        except Exception as e:
            logger.error(f"schema validation failed on raw output: {raw[:500]}")
            raise LLMGenerationException(f"llm output failed schema validation: {e}")


llm_service = LLMService()