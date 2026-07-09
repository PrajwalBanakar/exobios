package com.exobios.backend.referrals.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
public class AssignDoctorRequest {

    @NotNull(message = "doctorId is required")
    private UUID doctorId;
}
