package com.exobios.backend.referrals.dto;

import com.exobios.backend.referrals.entity.enums.ReferralPriority;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDate;

@Getter
@Setter
@NoArgsConstructor
public class UpdateReferralRequest {

    @Size(max = 200)
    private String referralHospital;

    @Size(max = 200)
    private String referralDoctor;

    private String referralReason;

    private ReferralPriority priority;

    private LocalDate followUpDate;
}
