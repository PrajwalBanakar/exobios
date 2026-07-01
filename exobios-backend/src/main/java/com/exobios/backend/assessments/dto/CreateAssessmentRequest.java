package com.exobios.backend.assessments.dto;

import com.exobios.backend.assessments.entity.enums.ComplaintCategory;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
public class CreateAssessmentRequest {

    @NotNull(message = "patientId is required")
    private UUID patientId;

    private String patientComplaint;

    private ComplaintCategory complaintCategory;

    /** ASHA always uses their own ID; SUPER_ADMIN may specify or leave null to inherit from the patient. */
    private UUID ashaWorkerId;

    /** Defaults to NOW() if not provided. */
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
