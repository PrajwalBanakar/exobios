from openai import OpenAI

from app.core.config import Settings, get_settings
from app.generation.providers.openai_provider import OpenAIProvider
from app.generation.services.generation_service import GenerationService
from app.generation.validation.response_validator import ResponseValidator


def build_default_generation_service(
    settings: Settings | None = None,
    openai_client: OpenAI | None = None,
) -> GenerationService:
    """Composition root wiring OpenAIProvider + ResponseValidator into a
    GenerationService. `openai_client` is injectable so tests (and
    alternative deployments) can supply a fake instead of a real network
    client built from `settings`. Constructing an `OpenAI` client performs
    no network I/O, and neither does anything else here — no external
    service is contacted during factory construction.
    """
    settings = settings or get_settings()

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
