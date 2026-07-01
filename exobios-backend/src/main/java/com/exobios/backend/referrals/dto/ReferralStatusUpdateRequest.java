package com.exobios.backend.referrals.dto;

import com.exobios.backend.referrals.entity.enums.ReferralStatus;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class ReferralStatusUpdateRequest {

    @NotNull(message = "status is required")
    private ReferralStatus status;
}
