from app.schemas.analyze import AiRequest, AiResponse, AiResultStatus

MODEL_VERSION = "stub-v0.1.0"
SOURCE = "exobios-ai-stub"

# AI-1 implements no clinical logic. `riskLevel` is left null rather than
# defaulted to LOW: RiskLevel is nullable end-to-end (AiResponse, the
# ai_assessment_results/assessments DB columns, and the CHECK constraints all
# permit NULL), and returning LOW here would falsely imply a patient was
# clinically triaged as low risk. `status=PENDING` mirrors the same value
# Java's own AiResponse.placeholder() uses while no real analysis exists.
_PLACEHOLDER_SUMMARY = "AI analysis pipeline is not implemented in this service version."


def generate_placeholder_response(request: AiRequest) -> AiResponse:
    return AiResponse(
        status=AiResultStatus.PENDING,
        summary=_PLACEHOLDER_SUMMARY,
        risk_level=None,
        confidence_score=0.0,
        red_flags="",
        recommendations="",
        model_version=MODEL_VERSION,
        source=SOURCE,
    )
