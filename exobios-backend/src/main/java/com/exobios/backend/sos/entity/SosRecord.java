package com.exobios.backend.sos.entity;

import com.exobios.backend.common.entity.BaseEntity;
import com.exobios.backend.sos.entity.enums.SosStatus;
import com.exobios.backend.sos.entity.enums.SosType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "sos_records")
@Getter
@Setter
@NoArgsConstructor
public class SosRecord extends BaseEntity {

    @Column(name = "patient_id", nullable = false)
    private UUID patientId;

    @Column(name = "assessment_id")
    private UUID assessmentId;

    @Column(name = "asha_worker_id", nullable = false)
    private UUID ashaWorkerId;

    @Enumerated(EnumType.STRING)
    @Column(name = "type", nullable = false, length = 30)
    private SosType type;

    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    @Column(name = "latitude", precision = 10, scale = 7)
    private BigDecimal latitude;

    @Column(name = "longitude", precision = 10, scale = 7)
    private BigDecimal longitude;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private SosStatus status = SosStatus.ACTIVE;

    @Column(name = "resolved_at")
    private Instant resolvedAt;
}
