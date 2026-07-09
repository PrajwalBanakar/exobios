package com.exobios.backend.referrals.entity;

import com.exobios.backend.common.entity.BaseEntity;
import com.exobios.backend.referrals.entity.enums.ReferralPriority;
import com.exobios.backend.referrals.entity.enums.ReferralReviewStage;
import com.exobios.backend.referrals.entity.enums.ReferralStatus;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "referrals")
@Getter
@Setter
@NoArgsConstructor
public class Referral extends BaseEntity {

    @Column(name = "assessment_id", nullable = false)
    private UUID assessmentId;

    @Column(name = "patient_id", nullable = false)
    private UUID patientId;

    @Column(name = "asha_worker_id", nullable = false)
    private UUID ashaWorkerId;

    @Column(name = "referral_hospital", length = 200)
    private String referralHospital;

    @Column(name = "referral_doctor", length = 200)
    private String referralDoctor;

    @Column(name = "referral_reason", columnDefinition = "TEXT", nullable = false)
    private String referralReason;

    @Enumerated(EnumType.STRING)
    @Column(name = "priority", nullable = false, length = 10)
    private ReferralPriority priority = ReferralPriority.MEDIUM;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private ReferralStatus status = ReferralStatus.PENDING;

    @Column(name = "follow_up_date")
    private LocalDate followUpDate;

    // ── Doctor review lifecycle (separate from `status`, which tracks the
    //    destination hospital's outcome) ────────────────────────────────
    @Enumerated(EnumType.STRING)
    @Column(name = "review_stage", nullable = false, length = 30)
    private ReferralReviewStage reviewStage = ReferralReviewStage.CREATED;

    @Column(name = "assigned_doctor_id")
    private UUID assignedDoctorId;

    @Column(name = "doctor_recommendation", columnDefinition = "TEXT")
    private String doctorRecommendation;
}
