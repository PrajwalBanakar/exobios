import logging

from fastapi import APIRouter, Depends

from api.dependencies import check_rate_limit, verify_api_key
from graph.builder import assessment_graph
from repositories.persistence import persist_state
from schemas.request import AiRequest
from schemas.response import AssessmentResponse
from schemas.state_object import AssessmentState

router = APIRouter()
logger = logging.getLogger("app.analyze")


@router.post(
    "/analyze",
    response_model=AssessmentResponse,
    # Order matters: auth first, so an invalid key is rejected before ever
    # touching the rate limiter (see check_rate_limit's docstring).
    dependencies=[Depends(verify_api_key), Depends(check_rate_limit)],
)
def analyze(request: AiRequest) -> AssessmentResponse:
    # Do NOT reassign the request-scoped id here — RequestContextMiddleware
    # already set it (reusing the caller's X-Request-Id when present) and
    # also uses it for the response header. Overwriting it mid-request made
    # the header and the logs disagree on the id for the same request.
    logger.info(f"starting analysis for assessment_id={request.assessment_id}")

    initial_state = AssessmentState(assessment_id=request.assessment_id, patient_input=request)

    final_state_dict = assessment_graph.invoke(initial_state)
    final_state = AssessmentState.model_validate(final_state_dict)

    persist_state(final_state, "final")

    logger.info(f"analysis complete for assessment_id={request.assessment_id}")
    return AssessmentResponse.from_state(final_state)