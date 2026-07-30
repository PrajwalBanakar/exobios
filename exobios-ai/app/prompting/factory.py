from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import Settings, get_settings
from app.prompting.builders.rag_prompt_builder import RagPromptBuilder
from app.prompting.formatting.context_formatter import ContextFormatter
from app.prompting.models.prompt import PromptTemplateName
from app.prompting.services.prompt_service import PromptService
from app.retrieval.services.retrieval_service import RetrievalService

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def build_default_prompt_service(
    retrieval_service: RetrievalService,
    settings: Settings | None = None,
) -> PromptService:
    """Composition root wiring RagPromptBuilder + ContextFormatter into a
    PromptService. Takes an already-built RetrievalService rather than
    constructing one itself — retrieval wiring (OpenAI/Qdrant clients) is
    AI-4's composition root's job (`app.retrieval.factory`), not this one's.
    """
    settings = settings or get_settings()

    jinja_env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(disabled_extensions=(".jinja2",), default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    builder = RagPromptBuilder(
        jinja_env=jinja_env,
        max_prompt_tokens=settings.max_prompt_tokens,
        max_context_tokens=settings.max_context_tokens,
        reserved_response_tokens=settings.reserved_response_tokens,
    )
    formatter = ContextFormatter()

    return PromptService(
        retrieval_service=retrieval_service,
        prompt_builder=builder,
        context_formatter=formatter,
        default_template=PromptTemplateName(settings.default_prompt_template),
    )
