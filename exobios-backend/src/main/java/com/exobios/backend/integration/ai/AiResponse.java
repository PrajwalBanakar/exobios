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

    /** Returned when the AI service is unavailable — sets status PENDING for later retry. */
    public static AiResponse placeholder() {
        return AiResponse.builder()
                .status(AiResultStatus.PENDING)
                .summary("AI analysis pending — service not yet available")
                .recommendations("Assessment has been queued for AI analysis once the service is online")
                .modelVersion("placeholder-v0")
                .source("placeholder")
                .build();
    }
}
