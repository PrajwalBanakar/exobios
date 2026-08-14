"""
single service file to handle all S3 uploads and DB writes
"""
import boto3
import mimetypes
from botocore.exceptions import ClientError
from boto3.exceptions import S3UploadFailedError
from config.settings import settings
from core.reporting import reporter
from schemas.step_result import StepResult, StepStatus

from core.supabase_client import supabase_client
from schemas.document_schema import DocumentMetadata, DocumentStatus

TABLE_NAME = "documents"
_s3_client = boto3.client('s3')

# Error messages are truncated before being persisted — a short, actionable
# reason belongs in the DB for operators to see at a glance; a full
# traceback (or, in principle, anything that happened to embed a secret)
# does not. The full exception is still logged normally via `logger.exception`
# at the call site in loaders/loader.py.
_MAX_ERROR_MESSAGE_LENGTH = 500


def upload_parsed_document_to_S3(parsed_file_str: str, object_name: str) -> bool:
    try:
        _s3_client.put_object(
            Bucket=settings.s3_bucket_name_parsed_doc,
            Key=object_name,
            Body=parsed_file_str.encode('utf-8'),
            ContentType="text/markdown",
        )
    except ClientError as e:
        reporter.report(StepResult(
            step_name="upload_to_S3_parsed",
            status=StepStatus.FAIL,
            error_message=str(e),
        ))
        return False

    reporter.report(StepResult(
        step_name="upload_to_S3_parsed",
        status=StepStatus.SUCCESS,
        data={"bucket": settings.s3_bucket_name_parsed_doc, "key": object_name},
    ))
    return True


def upload_raw_document_to_S3(local_filepath: str, object_name: str) -> bool:
    content_type, _ = mimetypes.guess_type(local_filepath)
    extra_args = {"ContentType": content_type} if content_type else {}
    try:
        _s3_client.upload_file(
            Filename=local_filepath,
            Bucket=settings.s3_bucket_name_raw_doc,
            Key=object_name,
            ExtraArgs=extra_args,
        )
    except (ClientError, S3UploadFailedError) as e:
        reporter.report(StepResult(
            step_name="upload_to_S3_raw",
            status=StepStatus.FAIL,
            error_message=str(e),
        ))
        return False

    reporter.report(StepResult(
        step_name="upload_to_S3_raw",
        status=StepStatus.SUCCESS,
        data={"bucket": settings.s3_bucket_name_raw_doc, "key": object_name},
    ))
    return True


def save_document_metadata(metadata: DocumentMetadata) -> bool:
    try:
        # Upsert, not insert: document_id is now derived from a content hash
        # (see loaders/loader.py), so re-ingesting identical file content
        # deliberately hits the same primary key. That must be a no-op
        # update, not a duplicate-key failure that aborts the run.
        supabase_client.table(TABLE_NAME).upsert(metadata.model_dump(), on_conflict="document_id").execute()
    except Exception as e:
        reporter.report(StepResult(
            step_name="save_document_metadata",
            status=StepStatus.FAIL,
            error_message=str(e),
        ))
        return False

    reporter.report(StepResult(
        step_name="save_document_metadata",
        status=StepStatus.SUCCESS,
        data={"document_id": metadata.document_id, "title": metadata.document_title},
    ))
    return True


def update_document_status(document_id: str, status: DocumentStatus, error_message: str | None = None) -> bool:
    """Targeted status-only update — does not require re-supplying every
    DocumentMetadata field like save_document_metadata's upsert does. Used
    by loaders/loader.py to move a document PROCESSING -> COMPLETED/FAILED
    once the full pipeline (chunk, embed, Qdrant upsert) has actually
    finished, not just after metadata was written."""
    truncated = error_message[:_MAX_ERROR_MESSAGE_LENGTH] if error_message else None
    try:
        supabase_client.table(TABLE_NAME).update(
            {"status": status.value, "error_message": truncated}
        ).eq("document_id", document_id).execute()
    except Exception as e:
        reporter.report(StepResult(
            step_name="update_document_status",
            status=StepStatus.FAIL,
            error_message=str(e),
        ))
        return False

    reporter.report(StepResult(
        step_name="update_document_status",
        status=StepStatus.SUCCESS,
        data={"document_id": document_id, "new_status": status.value},
    ))
    return True


def find_active_versions(logical_document_key: str, exclude_document_id: str) -> list[str]:
    """Returns document_ids of other COMPLETED, currently-active rows
    sharing this logical_document_key — i.e. prior versions of the same
    document that a newly-completed ingestion should supersede. Excludes
    exclude_document_id (the version currently being ingested) in case this
    is itself a retry/re-run rather than a genuinely new version."""
    try:
        response = (
            supabase_client.table(TABLE_NAME)
            .select("document_id")
            .eq("logical_document_key", logical_document_key)
            .eq("is_active", True)
            .eq("status", DocumentStatus.COMPLETED.value)
            .neq("document_id", exclude_document_id)
            .execute()
        )
        return [row["document_id"] for row in (response.data or [])]
    except Exception as e:
        reporter.report(StepResult(step_name="find_active_versions", status=StepStatus.FAIL, error_message=str(e)))
        return []


def mark_superseded(document_id: str, superseded_by: str) -> bool:
    """Deactivates a prior version's metadata row — never touches Qdrant
    vectors (see the migration's comment for why deletion is out of scope
    here). Called only after the new version has already reached COMPLETED,
    so a failed re-ingestion never deactivates a working prior version."""
    try:
        supabase_client.table(TABLE_NAME).update(
            {"is_active": False, "superseded_by": superseded_by}
        ).eq("document_id", document_id).execute()
    except Exception as e:
        reporter.report(StepResult(step_name="mark_superseded", status=StepStatus.FAIL, error_message=str(e)))
        return False

    reporter.report(StepResult(
        step_name="mark_superseded",
        status=StepStatus.SUCCESS,
        data={"document_id": document_id, "superseded_by": superseded_by},
    ))
    return True