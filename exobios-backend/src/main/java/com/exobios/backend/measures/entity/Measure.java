package com.exobios.backend.measures.entity;

import com.exobios.backend.common.entity.BaseEntity;
import com.exobios.backend.measures.entity.enums.MeasureCategory;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "measures")
@Getter
@Setter
@NoArgsConstructor
public class Measure extends BaseEntity {

    @Column(name = "assessment_id", nullable = false)
    private UUID assessmentId;

    @Column(name = "patient_id", nullable = false)
    private UUID patientId;

    @Column(name = "asha_worker_id", nullable = false)
    private UUID ashaWorkerId;

    @Column(name = "action", nullable = false, length = 200)
    private String action;

    @Enumerated(EnumType.STRING)
    @Column(name = "category", length = 50)
    private MeasureCategory category;

    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    @Column(name = "implemented_at", nullable = false)
    private Instant implementedAt;

    @Column(name = "implemented_by", length = 200)
    private String implementedBy;

    @Column(name = "outcome", columnDefinition = "TEXT")
    private String outcome;

    @Column(name = "notes", columnDefinition = "TEXT")
    private String notes;
}
