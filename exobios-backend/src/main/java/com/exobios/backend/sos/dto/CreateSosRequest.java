package com.exobios.backend.sos.dto;

import com.exobios.backend.sos.entity.enums.SosType;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;
import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
public class CreateSosRequest {

    @NotNull(message = "patientId is required")
    private UUID patientId;

    private UUID assessmentId;

    @NotNull(message = "SOS type is required")
    private SosType type;

    private String description;

    @DecimalMin(value = "-90.0",  message = "latitude must be between -90 and 90")
    @DecimalMax(value = "90.0",   message = "latitude must be between -90 and 90")
    private BigDecimal latitude;

    @DecimalMin(value = "-180.0", message = "longitude must be between -180 and 180")
    @DecimalMax(value = "180.0",  message = "longitude must be between -180 and 180")
    private BigDecimal longitude;
}
