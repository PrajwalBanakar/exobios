package com.exobios.backend.referrals.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class RecommendationRequest {

    @NotBlank(message = "recommendation is required")
    private String recommendation;
}
