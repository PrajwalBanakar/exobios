package com.exobios.backend.assessments.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class SymptomRequest {

    @NotBlank(message = "Symptom name is required")
    @Size(max = 200, message = "Symptom name must not exceed 200 characters")
    private String name;

    @Size(max = 100, message = "Duration must not exceed 100 characters")
    private String duration;

    @Size(max = 20, message = "Severity must not exceed 20 characters")
    private String severity;

    private String remarks;
}
