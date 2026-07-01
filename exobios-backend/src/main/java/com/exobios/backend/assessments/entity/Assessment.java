package com.exobios.backend.assessments.entity;

import com.exobios.backend.assessments.entity.enums.AssessmentStatus;
import com.exobios.backend.assessments.entity.enums.ComplaintCategory;
import com.exobios.backend.assessments.entity.enums.RiskLevel;
import com.exobios.backend.common.entity.BaseEntity;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "assessments")
@Getter
@Setter
@NoArgsConstructor
public class Assessment extends BaseEntity {

    @Column(name = "assessment_number", unique = true, nullable = false, length = 20)
    private String assessmentNumber;

    @Column(name = "patient_id", nullable = false)
    private UUID patientId;

    @Column(name = "asha_worker_id", nullable = false)
    private UUID ashaWorkerId;

    @Column(name = "patient_complaint", columnDefinition = "TEXT")
    private String patientComplaint;

    @Enumerated(EnumType.STRING)
    @Column(name = "complaint_category", length = 50)
    private ComplaintCategory complaintCategory;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private AssessmentStatus status = AssessmentStatus.DRAFT;

    @Enumerated(EnumType.STRING)
    @Column(name = "risk_level", length = 10)
    private RiskLevel riskLevel;

    @Column(name = "assessed_at", nullable = false)
    private Instant assessedAt;

    @Column(name = "submitted_at")
    private Instant submittedAt;

    // ── Relationships ──────────────────────────────────────────────

    @OneToMany(mappedBy = "assessment", cascade = CascadeType.ALL,
               orphanRemoval = true, fetch = FetchType.LAZY)
    private List<Symptom> symptoms = new ArrayList<>();

    @OneToOne(mappedBy = "assessment", cascade = CascadeType.ALL,
              fetch = FetchType.LAZY)
    private Vitals vitals;

    @OneToOne(mappedBy = "assessment", cascade = CascadeType.ALL,
              fetch = FetchType.LAZY)
    private MedicalHistory medicalHistory;

    @OneToOne(mappedBy = "assessment", cascade = CascadeType.ALL,
              fetch = FetchType.LAZY)
    private ExaminationFinding examinationFinding;

    @OneToOne(mappedBy = "assessment", cascade = CascadeType.ALL,
              fetch = FetchType.LAZY)
    private LegacyInformation legacyInformation;

    @OneToOne(mappedBy = "assessment", cascade = CascadeType.ALL,
              fetch = FetchType.LAZY)
    private AiAssessmentResult aiResult;
}
