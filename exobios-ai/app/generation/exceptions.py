from app.core.exceptions import AppError

# Status code choices, documented here since they're not obvious from the
# HTTP spec alone:
#
# - ProviderUnavailableError   502  the provider (or network) is unreachable
#                                   or returned a server-side error; retrying
#                                   later may help.
# - ProviderAuthenticationError 500 OUR OpenAI credentials/config are invalid
#                                   — unlike AI-1's AuthenticationError (401,
#                                   a caller-of-us problem), this is our own
#                                   infrastructure misconfiguration, not the
#                                   caller's fault.
# - ProviderRateLimitError     429  passed through as-is so retry-aware
#                                   callers can back off.
# - ProviderTimeoutError       504  the provider took too long to respond.
# - ProviderRefusalError       422  the model understood the request but
#                                   declined to produce clinical output
#                                   (content-policy refusal) — a valid,
#                                   well-formed outcome, not a transport
#                                   failure.
# - EmptyModelResponseError    502  the provider returned no usable output
#                                   at all.
# - StructuredOutputError      502  the provider's output didn't match the
#                                   requested schema (truncated/malformed).
# - GenerationValidationError  422  our own deterministic validation (not
#                                   the provider) rejected an otherwise
#                                   well-formed structured response.
# - PromptBudgetExceededError  413  prompt + reserved output tokens exceed
#                                   the configured model context window.
# - GenerationError            500  base class / generic catch-all wrapping
#                                   of anything not covered above.


class GenerationError(AppError):
    """Base class for all LLM-generation errors."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(status_code=status_code, code=code, message=message)


class ProviderUnavailableError(GenerationError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=502,
            code="PROVIDER_UNAVAILABLE",
            message=f"LLM provider unavailable: {reason}",
        )


class ProviderAuthenticationError(GenerationError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=500,
            code="PROVIDER_AUTHENTICATION_ERROR",
            message=f"LLM provider authentication failed: {reason}",
        )


class ProviderRateLimitError(GenerationError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=429,
            code="PROVIDER_RATE_LIMITED",
            message=f"LLM provider rate limit exceeded: {reason}",
        )


class ProviderTimeoutError(GenerationError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=504,
            code="PROVIDER_TIMEOUT",
            message=f"LLM provider request timed out: {reason}",
        )


class ProviderRefusalError(GenerationError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=422,
            code="PROVIDER_REFUSAL",
            message=f"LLM provider declined to generate a response: {reason}",
        )


class EmptyModelResponseError(GenerationError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=502,
            code="EMPTY_MODEL_RESPONSE",
            message=f"LLM provider returned no usable output: {reason}",
        )


class StructuredOutputError(GenerationError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=502,
            code="STRUCTURED_OUTPUT_ERROR",
            message=f"LLM provider returned malformed structured output: {reason}",
        )


class GenerationValidationError(GenerationError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=422,
            code="GENERATION_VALIDATION_ERROR",
            message=f"Generated clinical output failed validation: {reason}",
        )


class PromptBudgetExceededError(GenerationError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            status_code=413,
            code="PROMPT_BUDGET_EXCEEDED",
            message=f"Prompt exceeds the configured token budget: {reason}",
        )
