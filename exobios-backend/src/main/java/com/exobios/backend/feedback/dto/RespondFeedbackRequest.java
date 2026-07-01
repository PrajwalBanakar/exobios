package com.exobios.backend.feedback.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class RespondFeedbackRequest {

    @NotBlank(message = "response is required")
    private String response;
}
