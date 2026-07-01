package com.exobios.backend.assessments.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.UUID;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class VitalsDto {
    private UUID       id;
    private Integer    heartRate;
    private BigDecimal spo2;
    private BigDecimal temperature;
    private Integer    bloodPressureSystolic;
    private Integer    bloodPressureDiastolic;
    private Integer    respiratoryRate;
    private BigDecimal height;
    private BigDecimal weight;
    private BigDecimal bmi;
    private BigDecimal bloodSugar;
}
