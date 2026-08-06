import logging

from core.reporting.base import Reporter
from schemas.step_result import StepResult, StepStatus

logger = logging.getLogger("app.reporter")


class FileReporter(Reporter):
    """Logs each StepResult as one readable line: step name, status, and
    either the key data fields or the error message. Kept human-scannable
    in app.log rather than raw JSON blobs."""

    def report(self, result: StepResult) -> None:
        if result.status == StepStatus.SUCCESS:
            data_str = ", ".join(f"{k}={v}" for k, v in (result.data or {}).items())
            logger.info(f"[OK] {result.step_name} | {data_str}")
        else:
            logger.error(f"[FAIL] {result.step_name} | {result.error_message}")