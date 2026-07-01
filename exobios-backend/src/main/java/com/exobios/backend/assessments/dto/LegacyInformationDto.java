package com.exobios.backend.assessments.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.UUID;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LegacyInformationDto {
    private UUID   id;
    private String familySupport;
    private String livingConditions;
    private String previousInterventions;
    private String notes;
}
