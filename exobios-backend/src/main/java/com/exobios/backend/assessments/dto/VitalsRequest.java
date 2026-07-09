package com.exobios.backend.assessments.dto;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;

@Getter
@Setter
@NoArgsConstructor
public class VitalsRequest {

    @Min(value = 20,  message = "Heart rate must be at least 20 bpm")
    @Max(value = 300, message = "Heart rate must not exceed 300 bpm")
    private Integer heartRate;

    @DecimalMin(value = "0.0",   message = "SpO2 must be at least 0")
    @DecimalMax(value = "100.0", message = "SpO2 must not exceed 100")
    private BigDecimal spo2;

    @DecimalMin(value = "30.0",  message = "Temperature must be at least 30°C")
    @DecimalMax(value = "45.0",  message = "Temperature must not exceed 45°C")
    private BigDecimal temperature;

    @Min(value = 50,  message = "Systolic BP must be at least 50 mmHg")
    @Max(value = 300, message = "Systolic BP must not exceed 300 mmHg")
    private Integer bloodPressureSystolic;

    @Min(value = 20,  message = "Diastolic BP must be at least 20 mmHg")
    @Max(value = 200, message = "Diastolic BP must not exceed 200 mmHg")
    private Integer bloodPressureDiastolic;

    @Min(value = 5,   message = "Respiratory rate must be at least 5 breaths/min")
    @Max(value = 100, message = "Respiratory rate must not exceed 100 breaths/min")
    private Integer respiratoryRate;

    @DecimalMin(value = "30.0",   message = "Height must be at least 30 cm")
    @DecimalMax(value = "250.0",  message = "Height must not exceed 250 cm")
    private BigDecimal height;

    @DecimalMin(value = "1.0",    message = "Weight must be at least 1 kg")
    @DecimalMax(value = "500.0",  message = "Weight must not exceed 500 kg")
    private BigDecimal weight;

    @DecimalMin(value = "5.0",   message = "BMI must be at least 5")
    @DecimalMax(value = "100.0", message = "BMI must not exceed 100")
    private BigDecimal bmi;

    @DecimalMin(value = "0.0",    message = "Blood sugar must be at least 0 mg/dL")
    @DecimalMax(value = "1000.0", message = "Blood sugar must not exceed 1000 mg/dL")
    private BigDecimal bloodSugar;
}
