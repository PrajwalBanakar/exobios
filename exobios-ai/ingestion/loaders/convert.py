from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

from docling_core.types.doc import DoclingDocument
from pathlib import Path
import logging

from core.reporting import reporter
import logging

from exceptions import DocumentConversionError
from schemas.step import StepResult, StepStatus


logger = logging.getLogger(__name__)

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True

_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options = pipeline_options)
    }
)

def convert_to_docling_document(file_path: Path) -> DoclingDocument:

    try:
        dd = _converter.convert(file_path)
        dd_doc = dd.document
        
        reporter.report(StepResult(step_name="convert",
            status=StepStatus.SUCCESS,
            data={"file": str(file_path)},
            ))
    
        return dd_doc
    except DocumentConversionError as e:
        reporter.report(StepResult(
            step_name="convert",
            status=StepStatus.FAIL,
            error_message=str(e),
        ))
        return None
    except Exception as e:
        logger.exception(f"Unclassified error converting {file_path}")
        reporter.report(StepResult(
            step_name="convert",
            status=StepStatus.FAIL,
            error_message=f"UNCLASSIFIED: {e}",
        ))
        return None