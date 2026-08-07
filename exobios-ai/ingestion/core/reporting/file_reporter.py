import logging
from .base import Reporter
from schemas.step import StepResult, StepStatus


logger = logging.getLogger("ingestion.reporter")

class FileReporter(Reporter):
    def report(self, result: StepResult) -> None:
        if result.status == StepStatus.SUCCESS:
            logger.info(result.model_dump_json())
        else:
            logger.error(result.model_dump_json())