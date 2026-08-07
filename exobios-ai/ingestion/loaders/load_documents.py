from pathlib import Path
from typing import Iterator
import logging

from exceptions import DocumentDiscoveryError
from core.reporting import reporter
from schemas.step import StepResult, StepStatus

logger = logging.getLogger(__name__)

# for now loading from doc folder, in future might read from external sources (cloud)
def load_documents(folder_path: Path) -> Iterator[Path]:
    try:
        for file in folder_path.iterdir():
            if file.is_file():
                yield file

    except DocumentDiscoveryError as e:
        reporter.report(StepResult(
            step_name="document_loader",
            status=StepStatus.FAIL,
            error_message=str(e),
        ))
        raise

    except Exception as e:
        logger.exception(f"Unclassified error discovering documents in {folder_path}")
        reporter.report(StepResult(
            step_name="document_loader",
            status=StepStatus.FAIL,
            error_message=f"UNCLASSIFIED: {e}",
        ))
        raise DocumentDiscoveryError(folder_path=str(folder_path), reason=str(e))