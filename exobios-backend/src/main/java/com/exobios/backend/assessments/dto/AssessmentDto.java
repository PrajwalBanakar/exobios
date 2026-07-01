package com.exobios.backend.assessments.dto;

import com.exobios.backend.assessments.entity.enums.AssessmentStatus;
import com.exobios.backend.assessments.entity.enums.ComplaintCategory;
import com.exobios.backend.assessments.entity.enums.RiskLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AssessmentDto {
    private UUID                    id;
    private String                  assessmentNumber;
    private UUID                    patientId;
    private UUID                    ashaWorkerId;
    private String                  patientComplaint;
    private ComplaintCategory       complaintCategory;
    private AssessmentStatus        status;
    private RiskLevel               riskLevel;
    private Instant                 assessedAt;
    private Instant                 submittedAt;
    private Instant                 createdAt;
    private Instant                 updatedAt;
    private List<SymptomDto>        symptoms;
    private VitalsDto               vitals;
    private MedicalHistoryDto       medicalHistory;
    private ExaminationFindingDto   examinationFinding;
    private LegacyInformationDto    legacyInformation;
    private AiAssessmentResultDto   aiResult;
}
