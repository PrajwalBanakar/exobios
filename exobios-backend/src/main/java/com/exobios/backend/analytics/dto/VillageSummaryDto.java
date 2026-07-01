package com.exobios.backend.analytics.dto;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class VillageSummaryDto {
    private String village;
    private String district;
    private long   patients;
    private long   assessments;
    private long   highRiskCases;
    private long   referrals;
}
