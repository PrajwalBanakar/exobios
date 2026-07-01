package com.exobios.backend.assessments.dto;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class LegacyInformationRequest {
    private String familySupport;
    private String livingConditions;
    private String previousInterventions;
    private String notes;
}
