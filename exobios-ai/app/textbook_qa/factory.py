from google import genai
from openai import OpenAI
from qdrant_client import QdrantClient

from app.core.config import Settings, get_settings
from app.prompting.formatting.context_formatter import ContextFormatter
from app.retrieval.factory import build_default_retrieval_service
from app.textbook_qa.models import GroundingMode
from app.textbook_qa.prompt_builder import TextbookPromptBuilder
from app.textbook_qa.providers import (
    GeminiTextbookProvider,
    OpenAITextbookProvider,
    TextbookLLMProvider,
)
from app.textbook_qa.service import TextbookQAService
from app.textbook_qa.validator import TextbookAnswerValidator


def build_default_textbook_qa_service(
    settings: Settings | None = None,
    openai_client: OpenAI | None = None,
    gemini_client: genai.Client | None = None,
    qdrant_client: QdrantClient | None = None,
) -> TextbookQAService:
    """Composition root wiring RetrievalService (pointed at the textbook
    collection) + TextbookPromptBuilder + a TextbookLLMProvider (Gemini or
    OpenAI, matching whichever key is configured — same selection rule as
    every other factory in this codebase) + TextbookAnswerValidator into a
    TextbookQAService.

    The retrieval-service's own min_score is left at 0.0 deliberately: the
    meaningful STRICT-mode evidence threshold is enforced by
    TextbookQAService itself (settings.textbook_min_retrieval_score),
    *after* seeing the real top score — keeping raw scores visible is what
    lets --debug-retrieval show them even for a refused query.
    """
    settings = settings or get_settings()

    retrieval_service = build_default_retrieval_service(
        settings=settings,
        openai_client=openai_client,
        gemini_client=gemini_client,
        qdrant_client=qdrant_client,
        collection_name=settings.qdrant_textbook_collection,
        min_score=0.0,
    )

    prompt_builder = TextbookPromptBuilder(context_formatter=ContextFormatter())

    provider: TextbookLLMProvider
    if settings.gemini_api_key:
        client = gemini_client or genai.Client(api_key=settings.gemini_api_key)
        provider = GeminiTextbookProvider(
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
        provider = OpenAITextbookProvider(
            client=client,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_output_tokens,
            timeout_seconds=settings.llm_timeout_seconds,
        )

    validator = TextbookAnswerValidator()

    return TextbookQAService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        provider=provider,
        validator=validator,
        grounding_mode=GroundingMode(settings.knowledge_grounding_mode),
        min_retrieval_score=settings.textbook_min_retrieval_score,
    )
