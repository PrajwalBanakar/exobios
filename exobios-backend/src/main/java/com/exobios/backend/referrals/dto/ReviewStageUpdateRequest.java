package com.exobios.backend.referrals.dto;

import com.exobios.backend.referrals.entity.enums.ReferralReviewStage;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class ReviewStageUpdateRequest {

    @NotNull(message = "reviewStage is required")
    private ReferralReviewStage reviewStage;
}
