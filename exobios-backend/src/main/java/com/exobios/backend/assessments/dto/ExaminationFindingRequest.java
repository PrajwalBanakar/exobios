package com.exobios.backend.assessments.dto;

import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class ExaminationFindingRequest {
    private String generalAppearance;

    @Size(max = 100, message = "Consciousness must not exceed 100 characters")
    private String consciousness;

    private String edema;
    private String skin;
    private String respiratory;
    private String cardiovascular;
    private String abdominal;
    private String neurological;
}
