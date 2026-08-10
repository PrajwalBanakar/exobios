from app.core.exceptions import AppError


class TextbookQAError(AppError):
    """Base class for textbook Q&A errors."""


class UnsupportedGroundingModeError(TextbookQAError):
    def __init__(self, mode: str) -> None:
        self.mode = mode
        super().__init__(
            status_code=501,
            code="UNSUPPORTED_GROUNDING_MODE",
            message=f"Grounding mode '{mode}' is not implemented yet (only STRICT is supported)",
        )


class TextbookAnswerValidationError(TextbookQAError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=422,
            code="TEXTBOOK_ANSWER_VALIDATION_ERROR",
            message=f"Textbook answer failed validation: {reason}",
        )
