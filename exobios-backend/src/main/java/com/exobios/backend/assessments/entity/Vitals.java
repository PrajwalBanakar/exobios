package com.exobios.backend.assessments.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;
import java.util.UUID;

@Entity
@Table(name = "vitals")
@Getter
@Setter
@NoArgsConstructor
public class Vitals {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", updatable = false, nullable = false)
    private UUID id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "assessment_id", nullable = false, unique = true)
    private Assessment assessment;

    @Column(name = "heart_rate")
    private Integer heartRate;

    @Column(name = "spo2", precision = 5, scale = 2)
    private BigDecimal spo2;

    // Fahrenheit — see VitalsRequest.temperature's doc comment for why (this
    // column previously had no unit documented at all and was validated as
    // Celsius one layer up, contradicting the frontend and the AI service).
    @Column(name = "temperature", precision = 5, scale = 2)
    private BigDecimal temperature;

    @Column(name = "blood_pressure_systolic")
    private Integer bloodPressureSystolic;

    @Column(name = "blood_pressure_diastolic")
    private Integer bloodPressureDiastolic;

    @Column(name = "respiratory_rate")
    private Integer respiratoryRate;

    @Column(name = "height", precision = 6, scale = 2)
    private BigDecimal height;

    @Column(name = "weight", precision = 6, scale = 2)
    private BigDecimal weight;

    @Column(name = "bmi", precision = 5, scale = 2)
    private BigDecimal bmi;

    @Column(name = "blood_sugar", precision = 7, scale = 2)
    private BigDecimal bloodSugar;
}
