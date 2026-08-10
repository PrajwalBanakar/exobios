class AppException(Exception):
    status_code: int = 500
    error_code: str = "internal_error"

class RetrievalException(AppException):
    status_code = 502
    error_code = "retrieval_failed"

class LLMGenerationException(AppException):
    status_code = 502
    error_code = "llm_generation_failed"

class InsufficientEvidenceException(AppException):
    status_code = 200
    error_code = "insufficient_evidence"