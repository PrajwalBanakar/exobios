package com.exobios.backend.sos.dto;

import com.exobios.backend.sos.entity.enums.SosStatus;
import com.exobios.backend.sos.entity.enums.SosType;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SosRecordDto {
    private UUID       id;
    private UUID       patientId;
    private UUID       assessmentId;
    private UUID       ashaWorkerId;
    private SosType    type;
    private String     description;
    private BigDecimal latitude;
    private BigDecimal longitude;
    private SosStatus  status;
    private Instant    resolvedAt;
    private Instant    createdAt;
    private Instant    updatedAt;
}
