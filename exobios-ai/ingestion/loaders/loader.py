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

import hashlib
import uuid
import logging
from pathlib import Path

from .load_documents import load_documents
from core.reporting import reporter
from schemas.step_result import StepResult, StepStatus

from schemas.document_schema import DocumentMetadata, DocumentStatus
from exceptions import DocumentDiscoveryError, DocumentConversionError
from .convert import convert_to_docling_document
from .classify_documents import classify
from services.upload import (
    upload_parsed_document_to_S3, upload_raw_document_to_S3,
    save_document_metadata, update_document_status,
    find_active_versions, mark_superseded,
)
from chunkers.chunker import chunk_docling_document
from embedder.embedder import embed_chunks, build_metadata_payloads
from store.qdrant_store import store_metadata_payloads

logger = logging.getLogger(__name__)

# Fixed namespace for deriving document ids from content hashes — do not
# change; see chunkers/chunker.py's matching note on _CHUNK_ID_NAMESPACE.
_DOCUMENT_ID_NAMESPACE = uuid.UUID("3f2504e0-4f89-41d3-9a0c-0305e82c3301")


def _compute_document_id(file_path: Path) -> tuple[str, str]:
    """Returns (document_id, content_hash_hex). document_id is a deterministic
    uuid5 derived from the file's content hash, so re-ingesting byte-identical
    content always yields the same document_id/chunk ids (see chunker.py) —
    the basis for idempotent re-ingestion. Different content, even under the
    same filename, is treated as a distinct document."""
    content_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
    document_id = str(uuid.uuid5(_DOCUMENT_ID_NAMESPACE, content_hash))
    return document_id, content_hash


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
        # None until the metadata row actually exists — a failure before
        # that point (e.g. a bad file that can't even be read/hashed) has
        # nothing in Supabase to mark FAILED, so it's log-only, same as
        # before this status lifecycle existed.
        doc_id: str | None = None
        try:
            doc_id, content_hash = _compute_document_id(file_path)
            docling_document = convert_to_docling_document(file_path)
            logger.info(f"converted {file_path.name}: {len(docling_document.pages)} page(s)")

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
                content_hash=content_hash,
                status=DocumentStatus.PROCESSING,
                # Default heuristic — see the versioning migration's comment.
                # Two different source files that happen to share a filename
                # stem would incorrectly be treated as versions of "the same"
                # document; an explicit, operator-supplied logical id would
                # avoid that, but is a product decision, not one to invent here.
                logical_document_key=file_path.stem,
            )

            # Metadata write happens before chunking/embedding/Qdrant, same as
            # before — but now its return value gates whether we proceed. If
            # this fails, we must not go on to produce vectors that would be
            # orphaned (no metadata row to belong to).
            if not save_document_metadata(metadata):
                logger.error(f"skipping {file_path.name}: failed to save document metadata, will not chunk/embed")
                continue

            storeParsedDocLocally(parsed_markdown, file_path)

            chunks = chunk_docling_document(docling_document, doc_id)

            vectors = embed_chunks(chunks)

            metadata_payloads = build_metadata_payloads(chunks, vectors, metadata)

            if not store_metadata_payloads(metadata_payloads):
                # document_id/chunk_id are deterministic (content-hash derived),
                # so this document is safely resumable: re-running the
                # pipeline over the same file will retry exactly this
                # document and upsert the missing vectors in place, without
                # duplicating anything that did make it into Qdrant.
                logger.error(
                    f"document {doc_id} ({file_path.name}) has a metadata row but Qdrant upsert "
                    "failed/partially failed — re-run ingestion on this file to complete it"
                )
                reporter.report(StepResult(
                    step_name="document_loading_main_loop",
                    status=StepStatus.FAIL,
                    error_message=f"qdrant upsert failed for document {doc_id}, metadata row already written",
                ))
                update_document_status(doc_id, DocumentStatus.FAILED, error_message="Qdrant upsert failed — re-run ingestion to retry")
                continue

            update_document_status(doc_id, DocumentStatus.COMPLETED)

            # Only now — after the NEW version is confirmed COMPLETED — may a
            # prior version of the same logical document be deactivated. If
            # this ingestion had failed instead, the prior (working) version
            # must stay active; that's why this runs last, not before the
            # pipeline started.
            for prior_doc_id in find_active_versions(metadata.logical_document_key, exclude_document_id=doc_id):
                mark_superseded(prior_doc_id, superseded_by=doc_id)
                logger.info(f"document {prior_doc_id} superseded by {doc_id} (logical_document_key={metadata.logical_document_key})")
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
            if doc_id is not None:
                # The metadata row exists (status=PROCESSING) but something
                # after that — chunking, embedding, or building payloads —
                # failed. Without this, the row would be stuck showing
                # PROCESSING forever, indistinguishable from "still running".
                update_document_status(doc_id, DocumentStatus.FAILED, error_message=str(e))
            continue


if __name__ == "__main__":
    run()