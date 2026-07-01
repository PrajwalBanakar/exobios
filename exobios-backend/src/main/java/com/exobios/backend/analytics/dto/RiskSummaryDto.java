package com.exobios.backend.analytics.dto;

import lombok.Builder;
import lombok.Getter;

import java.time.Instant;

@Getter
@Builder
public class RiskSummaryDto {
    private long    low;
    private long    medium;
    private long    high;
    private long    critical;
    private long    total;
    private Instant fromDate;
    private Instant toDate;
}
