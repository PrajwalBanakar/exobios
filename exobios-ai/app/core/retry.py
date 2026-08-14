import logging
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")
logger = logging.getLogger("app.retry")


def retry_with_backoff(
    fn: Callable[[], T],
    *,
    max_attempts: int = 2,
    base_delay: float = 1.0,
    is_retryable: Callable[[Exception], bool] = lambda e: True,
    op_name: str = "operation",
) -> T:
    """Retries `fn` with exponential backoff (base_delay * 2**attempt) on
    exceptions `is_retryable` accepts. Re-raises immediately on a
    non-retryable exception, and re-raises the last exception once attempts
    are exhausted. Intended for transient provider errors (connection
    resets, timeouts, 429/5xx) — never for deterministic failures like a
    schema-validation error, which retrying the same input will not fix."""
    last_exc: Exception
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if not is_retryable(e) or attempt == max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(f"{op_name} failed (attempt {attempt}/{max_attempts}): {e!r}. Retrying in {delay:.1f}s")
            time.sleep(delay)
    raise last_exc
