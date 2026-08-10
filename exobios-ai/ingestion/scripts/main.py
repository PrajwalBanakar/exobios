"""
run all services synchronously, efficiently
"""

from core.logging_config import setup_logging
from exceptions import IngestionError
import logging
from core.reporting import reporter
from schemas.step import StepResult, StepStatus

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

setup_logging()

from loaders.loader import run

def execute():
    try:
        run()
    except IngestionError as e:
        reporter.report(StepResult(
            step_name = "main_script",
            status= StepStatus.FAIL,
            data = {
                "error_message": str(e),
            }
        ))
    except Exception as e:
        logger.exception(f"UNCLASSIFIED EXCEPTION IN MAIN LOADER \n message: {str(e)}")
        reporter.report(StepResult(
            step_name = "main_script",
            status= StepStatus.FAIL,
            error_message=str(e)
        ))

if __name__ == "__main__":
    execute()