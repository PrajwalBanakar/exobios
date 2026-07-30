from abc import ABC, abstractmethod

from app.prompting.models.prompt import PromptContext, PromptResponse, PromptTemplateName


class PromptBuilder(ABC):
    """Common interface every prompt-assembly strategy implements. Swapping
    the section structure or templating approach means adding a new
    PromptBuilder subclass — PromptService depends only on this interface."""

    @abstractmethod
    def build(self, context: PromptContext, template: PromptTemplateName) -> PromptResponse: ...
