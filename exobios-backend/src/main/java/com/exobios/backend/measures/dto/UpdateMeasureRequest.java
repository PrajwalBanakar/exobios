package com.exobios.backend.measures.dto;

import com.exobios.backend.measures.entity.enums.MeasureCategory;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;

@Getter
@Setter
@NoArgsConstructor
public class UpdateMeasureRequest {

    @NotBlank(message = "action is required")
    @Size(max = 200, message = "action must not exceed 200 characters")
    private String action;

    private MeasureCategory category;

    private String description;

    private Instant implementedAt;

    @Size(max = 200)
    private String implementedBy;

    private String outcome;

    private String notes;
}
