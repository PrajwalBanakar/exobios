package com.exobios.backend.patients.dto;

import com.exobios.backend.patients.entity.enums.PatientStatus;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class ChangePatientStatusRequest {

    @NotNull(message = "Status is required")
    private PatientStatus status;
}
