package com.exobios.backend.referrals.dto;

import com.exobios.backend.referrals.entity.enums.ReferralPriority;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDate;
import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
public class CreateReferralRequest {

    @NotNull(message = "assessmentId is required")
    private UUID assessmentId;

    @Size(max = 200)
    private String referralHospital;

    @Size(max = 200)
    private String referralDoctor;

    @NotBlank(message = "referralReason is required")
    private String referralReason;

    private ReferralPriority priority = ReferralPriority.MEDIUM;

    private LocalDate followUpDate;
}
