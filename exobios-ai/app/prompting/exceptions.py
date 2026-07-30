from app.core.exceptions import AppError


class PromptBuildError(AppError):
    """Failure assembling the final prompt (template rendering, section
    composition), or any unexpected failure PromptService can't attribute
    to a more specific stage."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=500,
            code="PROMPT_BUILD_ERROR",
            message=f"Failed to build prompt: {reason}",
        )


class ContextFormattingError(AppError):
    """Failure deduplicating, sorting, or grouping retrieved chunks."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=500,
            code="CONTEXT_FORMATTING_ERROR",
            message=f"Failed to format retrieved context: {reason}",
        )
