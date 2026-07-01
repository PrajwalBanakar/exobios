package com.exobios.backend.devices.dto;

import com.exobios.backend.devices.entity.enums.DeviceType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class CreateDeviceRequest {

    @NotBlank(message = "deviceId is required")
    @Size(max = 100)
    private String deviceId;

    @NotBlank(message = "name is required")
    @Size(max = 200)
    private String name;

    @NotNull(message = "type is required")
    private DeviceType type;

    @Size(max = 100)
    private String model;
}
