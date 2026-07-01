package com.exobios.backend.referrals.dto;

import com.exobios.backend.referrals.entity.enums.ReferralPriority;
import com.exobios.backend.referrals.entity.enums.ReferralStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReferralDto {
    private UUID             id;
    private UUID             assessmentId;
    private UUID             patientId;
    private UUID             ashaWorkerId;
    private String           referralHospital;
    private String           referralDoctor;
    private String           referralReason;
    private ReferralPriority priority;
    private ReferralStatus   status;
    private LocalDate        followUpDate;
    private String           createdBy;
    private Instant          createdAt;
    private Instant          updatedAt;
}
