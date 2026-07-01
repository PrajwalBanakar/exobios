package com.exobios.backend.assessments.dto;

import com.exobios.backend.assessments.entity.enums.RiskLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiAssessmentResultDto {
    private UUID       id;
    private String     summary;
    private RiskLevel  riskLevel;
    private BigDecimal confidenceScore;
    private String     recommendations;
    private Instant    generatedAt;
    private String     source;
}
