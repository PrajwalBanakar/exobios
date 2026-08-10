import logging

from fastapi import APIRouter, Depends

from api.dependencies import verify_api_key
from core.logging_config import request_id_ctx
from graph.builder import assessment_graph
from repositories.persistence import persist_state
from schemas.request import AiRequest
from schemas.response import AssessmentResponse
from schemas.state_object import AssessmentState

router = APIRouter()
logger = logging.getLogger("app.analyze")


@router.post("/analyze", response_model=AssessmentResponse, dependencies=[Depends(verify_api_key)])
def analyze(request: AiRequest) -> AssessmentResponse:
    request_id_ctx.set(str(request.assessment_id))
    logger.info(f"starting analysis for assessment_id={request.assessment_id}")

    initial_state = AssessmentState(assessment_id=request.assessment_id, patient_input=request)

    final_state_dict = assessment_graph.invoke(initial_state)
    final_state = AssessmentState.model_validate(final_state_dict)

    persist_state(final_state, "final")

    logger.info(f"analysis complete for assessment_id={request.assessment_id}")
    return AssessmentResponse.from_state(final_state)