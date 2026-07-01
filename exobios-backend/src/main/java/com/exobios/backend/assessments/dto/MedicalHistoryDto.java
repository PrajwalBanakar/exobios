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
public class MedicalHistoryDto {
    private UUID   id;
    private String pastIllnesses;
    private String currentMedications;
    private String allergies;
    private String familyHistory;
    private String surgeryHistory;
    private String habits;
}
