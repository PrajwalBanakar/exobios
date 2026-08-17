from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

from docling_core.types.doc import DoclingDocument
from pathlib import Path
import logging

from core.reporting import reporter
import logging

from exceptions import DocumentConversionError
from schemas.step_result import StepResult, StepStatus


logger = logging.getLogger(__name__)

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True

_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options = pipeline_options)
    }
)

def convert_to_docling_document(file_path: Path) -> DoclingDocument:
    # Docling itself never raises our DocumentConversionError — it raises its
    # own exception types (corrupted PDF, unsupported format, OCR failure,
    # etc). Those are caught here and re-raised AS DocumentConversionError so
    # the caller (loaders/loader.py) gets one typed, catchable failure mode
    # instead of a None return that produces a misleading AttributeError two
    # lines later when the caller does docling_document.pages.
    try:
        dd = _converter.convert(file_path)
        dd_doc = dd.document

        reporter.report(StepResult(step_name="convert",
            status=StepStatus.SUCCESS,
            data={"file": str(file_path)},
            ))

        return dd_doc
    except Exception as e:
        logger.exception(f"Failed to convert {file_path}")
        reporter.report(StepResult(
            step_name="convert",
            status=StepStatus.FAIL,
            error_message=str(e),
        ))
        raise DocumentConversionError(str(file_path), str(e)) from e