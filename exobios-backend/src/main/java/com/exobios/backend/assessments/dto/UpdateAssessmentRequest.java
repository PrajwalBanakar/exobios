package com.exobios.backend.assessments.dto;

import com.exobios.backend.assessments.entity.enums.ComplaintCategory;
import jakarta.validation.Valid;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
public class UpdateAssessmentRequest {

    private String patientComplaint;

    private ComplaintCategory complaintCategory;

    private Instant assessedAt;

    @Valid
    private List<SymptomRequest> symptoms;

    @Valid
    private VitalsRequest vitals;

    @Valid
    private MedicalHistoryRequest medicalHistory;

    @Valid
    private ExaminationFindingRequest examinationFinding;

    @Valid
    private LegacyInformationRequest legacyInformation;
}
