from abc import ABC, abstractmethod

from app.generation.models.request import GenerationRequest
from app.generation.models.response import RawGenerationResponse


class LLMProvider(ABC):
    """Common interface every LLM backend implements. Swapping OpenAI for
    Azure OpenAI, Anthropic, Gemini, or a local model means adding a new
    LLMProvider subclass — GenerationService depends only on this interface
    and on project-owned models (GenerationRequest/RawGenerationResponse),
    never on any provider SDK's types.
    """

    @abstractmethod
    def generate_structured(self, request: GenerationRequest) -> RawGenerationResponse:
        """Generate a structured clinical draft. Must raise one of the
        exceptions in app.generation.exceptions for refusals, empty
        responses, malformed output, or provider-level failures — never
        return a partially-usable or unvalidated result."""

    @abstractmethod
    def health(self) -> bool:
        """A lightweight liveness check — must not perform an actual model
        generation call."""
