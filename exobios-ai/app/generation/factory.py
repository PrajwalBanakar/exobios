from google import genai
from openai import OpenAI

from app.core.config import Settings, get_settings
from app.generation.providers.base import LLMProvider
from app.generation.providers.gemini_provider import GeminiProvider
from app.generation.providers.openai_provider import OpenAIProvider
from app.generation.services.generation_service import GenerationService
from app.generation.validation.response_validator import ResponseValidator


def build_default_generation_service(
    settings: Settings | None = None,
    openai_client: OpenAI | None = None,
    gemini_client: genai.Client | None = None,
) -> GenerationService:
    """Composition root wiring an LLMProvider + ResponseValidator into a
    GenerationService. Builds GeminiProvider when GEMINI_API_KEY is
    configured (a free-tier alternative for local dev/demo use) and
    OpenAIProvider otherwise. `openai_client`/`gemini_client` are injectable
    so tests (and alternative deployments) can supply a fake instead of a
    real network client built from `settings`. Constructing either client
    performs no network I/O, and neither does anything else here — no
    external service is contacted during factory construction.
    """
    settings = settings or get_settings()

    provider: LLMProvider
    if settings.gemini_api_key:
        client = gemini_client or genai.Client(api_key=settings.gemini_api_key)
        provider = GeminiProvider(
            client=client,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_output_tokens,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    else:
        client = openai_client or OpenAI(
            api_key=settings.openai_api_key, max_retries=settings.llm_max_retries
        )
        provider = OpenAIProvider(
            client=client,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_output_tokens,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    validator = ResponseValidator()

    return GenerationService(
        provider=provider,
        validator=validator,
        context_window_tokens=settings.llm_context_window,
    )
