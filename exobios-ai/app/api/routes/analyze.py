import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import verify_api_key
from app.schemas.analyze import AiRequest, AiResponse
from app.services.analysis_service import generate_placeholder_response

router = APIRouter()
logger = logging.getLogger("app.analyze")


@router.post(
    "/analyze",
    response_model=AiResponse,
    dependencies=[Depends(verify_api_key)],
    tags=["analyze"],
)
async def analyze(payload: AiRequest) -> AiResponse:
    # Safe subset only: never log complaint text, symptom descriptions,
    # history, medications, allergies, or other patient-identifying details.
    logger.info(
        "assessment_id=%s complaint_category=%s symptom_count=%s vitals_provided=%s",
        payload.assessment_id,
        payload.complaint_category,
        len(payload.symptoms),
        payload.vitals is not None,
    )
    response = generate_placeholder_response(payload)
    logger.info("assessment_id=%s response_status=%s", payload.assessment_id, response.status)
    return response
