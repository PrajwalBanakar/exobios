package com.exobios.backend.devices.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
public class AssignDeviceRequest {

    @NotNull(message = "assignedTo (ASHA worker user ID) is required")
    private UUID assignedTo;
}
