package com.exobios.backend.analytics.dto;

import lombok.Builder;
import lombok.Getter;

import java.time.Instant;

@Getter
@Builder
public class ReferralSummaryDto {
    private long    total;
    // by status
    private long    pending;
    private long    accepted;
    private long    completed;
    private long    rejected;
    private long    cancelled;
    // by priority
    private long    priorityLow;
    private long    priorityMedium;
    private long    priorityHigh;
    private long    priorityUrgent;
    private Instant fromDate;
    private Instant toDate;
}
