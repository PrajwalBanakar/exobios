class AppError(Exception):
    """Base application error carrying an HTTP status and a stable error code."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class AuthenticationError(AppError):
    def __init__(self, message: str = "Missing or invalid API key") -> None:
        super().__init__(status_code=401, code="UNAUTHORIZED", message=message)
