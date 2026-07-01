package com.exobios.backend.integration.ai;

import com.exobios.backend.assessments.entity.Assessment;
import com.exobios.backend.assessments.entity.enums.ComplaintCategory;
import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Getter
@Builder
public class AiRequest {

    private UUID              assessmentId;
    private UUID              patientId;
    private String            patientComplaint;
    private ComplaintCategory complaintCategory;
    private List<SymptomSummary> symptoms;
    private VitalsSummary     vitals;
    private String            pastIllnesses;
    private String            currentMedications;
    private String            allergies;

    public static AiRequest from(Assessment assessment) {
        List<SymptomSummary> symptomSummaries = assessment.getSymptoms() == null ? List.of() :
                assessment.getSymptoms().stream()
                        .map(s -> SymptomSummary.builder()
                                .name(s.getName())
                                .duration(s.getDuration())
                                .severity(s.getSeverity())
                                .build())
                        .toList();

        VitalsSummary vitalsSummary = null;
        if (assessment.getVitals() != null) {
            var v = assessment.getVitals();
            vitalsSummary = VitalsSummary.builder()
                    .heartRate(v.getHeartRate())
                    .spo2(v.getSpo2())
                    .temperature(v.getTemperature())
                    .bloodPressureSystolic(v.getBloodPressureSystolic())
                    .bloodPressureDiastolic(v.getBloodPressureDiastolic())
                    .respiratoryRate(v.getRespiratoryRate())
                    .build();
        }

        String pastIllnesses = null;
        String currentMedications = null;
        String allergies = null;
        if (assessment.getMedicalHistory() != null) {
            pastIllnesses     = assessment.getMedicalHistory().getPastIllnesses();
            currentMedications = assessment.getMedicalHistory().getCurrentMedications();
            allergies         = assessment.getMedicalHistory().getAllergies();
        }

        return AiRequest.builder()
                .assessmentId(assessment.getId())
                .patientId(assessment.getPatientId())
                .patientComplaint(assessment.getPatientComplaint())
                .complaintCategory(assessment.getComplaintCategory())
                .symptoms(symptomSummaries)
                .vitals(vitalsSummary)
                .pastIllnesses(pastIllnesses)
                .currentMedications(currentMedications)
                .allergies(allergies)
                .build();
    }

    @Getter
    @Builder
    public static class SymptomSummary {
        private String name;
        private String duration;
        private String severity;
    }

    @Getter
    @Builder
    public static class VitalsSummary {
        private Integer    heartRate;
        private BigDecimal spo2;
        private BigDecimal temperature;
        private Integer    bloodPressureSystolic;
        private Integer    bloodPressureDiastolic;
        private Integer    respiratoryRate;
    }
}
