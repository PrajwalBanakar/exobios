package com.exobios.backend.analytics.dto;

import lombok.Builder;
import lombok.Getter;

import java.time.Instant;

@Getter
@Builder
public class DashboardDto {
    private long totalPatients;
    private long totalAshaWorkers;
    private long totalAssessments;
    private long totalReferrals;
    private long highCriticalRiskCount;
    private long pendingReferrals;
    private long measuresImplemented;
    private Instant generatedAt;
}
