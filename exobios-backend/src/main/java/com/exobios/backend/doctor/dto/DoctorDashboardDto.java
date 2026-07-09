package com.exobios.backend.doctor.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DoctorDashboardDto {
    private int assignedCount;
    private int underReviewCount;
    private int actionTakenCount;
    private int closedCount;
    private int unassignedInboxCount;
}
