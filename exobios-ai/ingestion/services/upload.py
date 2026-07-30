"""
single service file to handle all S3 uploads and DB writes
"""
import boto3
from botocore.exceptions import ClientError
from config.settings import settings
from core.reporting import reporter
from schemas.step_result import StepResult, StepStatus
from core.supabase_client import supabase_client

TABLE_NAME = "documents"
_s3_client = boto3.client('s3')


def upload_parsed_document_to_S3(parsed_file_str: str, object_name: str) -> bool:
    try:
        _s3_client.put_object(
            Bucket=settings.s3_bucket_name_parsed_doc,
            Key=object_name,
            Body=parsed_file_str.encode('utf-8'),
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
    try:
        _s3_client.upload_file(
            Filename=local_filepath,
            Bucket=settings.s3_bucket_name_raw_docs,
            Key=object_name,
        )
    except ClientError as e:
        reporter.report(StepResult(
            step_name="upload_to_S3_raw",
            status=StepStatus.FAIL,
            error_message=str(e),
        ))
        return False

    reporter.report(StepResult(
        step_name="upload_to_S3_raw",
        status=StepStatus.SUCCESS,
        data={"bucket": settings.s3_bucket_name_raw_docs, "key": object_name},
    ))
    return True


def save_document_metadata(metadata: DocumentMetadata) -> bool:
    try:
        supabase_client.table(TABLE_NAME).insert(metadata.model_dump()).execute()
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
