package com.exobios.backend.analytics.dto;

import lombok.Builder;
import lombok.Getter;

import java.util.UUID;

@Getter
@Builder
public class AshaPerformanceDto {
    private UUID   ashaWorkerId;
    private String ashaName;
    private String area;
    private String district;
    private long   patientsRegistered;
    private long   assessmentsCompleted;
    private long   measuresImplemented;
    private long   referralsMade;
    private long   highRiskCases;
}
