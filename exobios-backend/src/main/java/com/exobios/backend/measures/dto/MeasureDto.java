package com.exobios.backend.measures.dto;

import com.exobios.backend.measures.entity.enums.MeasureCategory;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.UUID;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MeasureDto {
    private UUID            id;
    private UUID            assessmentId;
    private UUID            patientId;
    private UUID            ashaWorkerId;
    private String          action;
    private MeasureCategory category;
    private String          description;
    private Instant         implementedAt;
    private String          implementedBy;
    private String          outcome;
    private String          notes;
    private Instant         createdAt;
    private Instant         updatedAt;
}
