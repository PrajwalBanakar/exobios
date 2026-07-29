"""
grab every document one by one from documents folder
for every document:
    generate a unique id
    send the doc to docling -- get back a docling document
    upload the dd to s3 -> get back a link/id of it from s3
    upload the raw doc as well to S3 -> get a link of it
    store in db : unique id <-> docling document s3 link <-> document title
    store in db : unique id <-> raw document s3 link <-> document title

    one more responsibility:
    build this:
         "document_id": "doc_moh_fever_guidelines_v3",
        "title": "Ministry of Health National Fever Management Guidelines",
        "issuing_authority": "Ministry of Health & Family Welfare",
        "version": "3.0",
        "publication_date": "2023-04-01",
"""

import uuid
import logging
from pathlib import Path

from .load_documents import load_documents
from core.reporting import reporter
from schemas.step_result import StepResult, StepStatus
from exceptions import DocumentDiscoveryError
from .convert import convert_to_docling_document

logger = logging.getLogger(__name__)


def run() -> None:
    folder_path = Path("documents")
    output_folder = folder_path / "docling_output"
    output_folder.mkdir(parents=True, exist_ok=True)  

    for file_path in load_documents(folder_path):
        try:
            doc_id = str(uuid.uuid4())
            docling_document = convert_to_docling_document(file_path)
            print(f"Number of pages: {len(docling_document.pages)}")
            output_path = output_folder / f"{file_path.stem}.md"
            output_path.write_text(docling_document.export_to_markdown(), encoding="utf-8")

            reporter.report(StepResult(
                step_name="document_loader_loop",
                status=StepStatus.SUCCESS,
                data={"doc_id": doc_id, "file": str(file_path), "output": str(output_path)},
            ))

        except DocumentDiscoveryError as e:
            reporter.report(StepResult(
                step_name="document_loading_main_loop",
                status=StepStatus.FAIL,
                error_message=str(e),
            ))
            continue

        except Exception as e:
            logger.exception("UNCLASSIFIED exception during document loading")
            reporter.report(StepResult(
                step_name="document_loading_main_loop",
                status=StepStatus.FAIL,
                error_message=f"UNCLASSIFIED: {e}",
            ))
            continue


if __name__ == "__main__":
    run()