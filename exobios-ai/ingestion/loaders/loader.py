"""
grab every document one by one from documents folder
for every document:
    generate a unique id
    send the doc to docling -- get back a docling document
    upload the dd to s3 -> get back a link/id of it from s3
    upload the raw doc as well to S3 -> get a link of it
    store in db : unique id <-> docling document s3 link (exported in some format) <-> document title
    store in db : unique id <-> raw document s3 link <-> document title
    store in db : the DocumentMetadata for this doc
"""

import uuid
import logging
from pathlib import Path

from .load_documents import load_documents
from core.reporting import reporter
from schemas.step import StepResult, StepStatus

from schemas.document_schema import DocumentMetadata
from exceptions import DocumentDiscoveryError
from .convert import convert_to_docling_document
from .classify_documents import classify
from services.upload import upload_parsed_document_to_S3, upload_raw_document_to_S3,save_document_metadata
from chunkers.chunker import chunk_docling_document
from embedder.embedder import embed_chunks, build_metadata_payloads 
from store.qdrant_store import store_metadata_payloads

logger = logging.getLogger(__name__)


def _pick_top_category(category_scores: dict) -> str:
    return max(category_scores, key=category_scores.get)


def _pick_applicable_roles(role_scores: dict, threshold: float = 0.5) -> list[str]:
    # tunable threshhold, if none are > threshhold just pick the highest
    roles = [role for role, score in role_scores.items() if score >= threshold]
    if not roles:
        roles = [max(role_scores, key=role_scores.get)]
    return roles


def storeParsedDocLocally(content: str, file_path: Path) -> None:
    folder_path = Path("documents")
    output_folder = folder_path / "docling_output"
    output_folder.mkdir(parents=True, exist_ok=True)
    output_path = output_folder / f"{file_path.stem}.md"
    output_path.write_text(content, encoding="utf-8")

def run() -> None:
    folder_path = Path("documents")
    

    for file_path in load_documents(folder_path):
        try:
            doc_id = str(uuid.uuid4())
            docling_document = convert_to_docling_document(file_path)
            print(f"Number of pages: {len(docling_document.pages)}")

            parsed_markdown = docling_document.export_to_markdown()
            
            classified = classify(docling_document)

            object_key = f"{doc_id}"
            # parsed_uploaded = upload_parsed_document_to_S3(parsed_markdown, object_key)
            # raw_uploaded = upload_raw_document_to_S3(str(file_path), object_key)

            # if not (parsed_uploaded and raw_uploaded):
            #     reporter.report(StepResult(
            #         step_name="document_loading_main_loop",
            #         status=StepStatus.FAIL,
            #         error_message=f"S3 upload failed for {file_path.name}, skipping DB write",
            #     ))
            #     continue

            metadata = DocumentMetadata(
                document_id=doc_id,
                document_title=classified["title"],
                complaint_category=_pick_top_category(classified["category_scores"]),
                applicable_roles=_pick_applicable_roles(classified["role_scores"]),
                file_location=object_key,  # same key, different bucket per artifact type
            )

            save_document_metadata(metadata)
            
            storeParsedDocLocally(parsed_markdown, file_path)
            
            chunks = chunk_docling_document(docling_document, doc_id)
            
            vectors = embed_chunks(chunks)
            
            metadata_payloads = build_metadata_payloads(chunks, vectors, metadata)
            
            store_metadata_payloads(metadata_payloads)
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