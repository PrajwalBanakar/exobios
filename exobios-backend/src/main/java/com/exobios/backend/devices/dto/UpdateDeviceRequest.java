package com.exobios.backend.devices.dto;

import com.exobios.backend.devices.entity.enums.DeviceStatus;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;

@Getter
@Setter
@NoArgsConstructor
public class UpdateDeviceRequest {

    @Size(max = 200)
    private String name;

    @Size(max = 100)
    private String model;

    private DeviceStatus status;

    @Min(0) @Max(100)
    private Integer batteryLevel;

    private Instant lastSyncedAt;
}
