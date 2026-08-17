package com.exobios.backend.integration.ai;

import com.exobios.backend.assessments.entity.enums.AiResultStatus;
import com.exobios.backend.assessments.entity.enums.RiskLevel;
import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;

@Getter
@Builder
public class AiResponse {

    private AiResultStatus status;
    private String         summary;
    private RiskLevel      riskLevel;
    private BigDecimal     confidenceScore;
    private String         redFlags;
    private String         recommendations;
    private String         modelVersion;
    private String         source;

    /**
     * Returned when the AI gateway could not produce a real result — every
     * attempt was exhausted (RestAiGateway) or the call threw
     * (AssessmentService.callAiGateway). Status is FAILED, not PENDING:
     * submitAssessment calls the gateway synchronously, so there is no
     * later moment where this would actually transition to COMPLETED on its
     * own — claiming PENDING implied a retry that was never going to
     * happen. riskLevel/confidenceScore/redFlags are deliberately left
     * null/empty rather than defaulted to anything that could read as a
     * real (e.g. LOW-risk) clinical judgment — an integration failure must
     * never be presentable as "the AI checked and it's fine."
     */
    public static AiResponse placeholder() {
        return AiResponse.builder()
                .status(AiResultStatus.FAILED)
                .summary("AI analysis could not be completed — the AI service was unavailable or returned an error")
                .recommendations("Assessment should be reviewed manually; AI analysis did not run")
                .modelVersion("unavailable")
                .source("exobios-ai-unavailable")
                .build();
    }
}
