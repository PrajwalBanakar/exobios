package com.exobios.backend.assessments.dto;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class MedicalHistoryRequest {
    private String pastIllnesses;
    private String currentMedications;
    private String allergies;
    private String familyHistory;
    private String surgeryHistory;
    private String habits;
}
