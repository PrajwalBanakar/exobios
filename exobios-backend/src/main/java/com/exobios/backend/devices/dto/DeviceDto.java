package com.exobios.backend.devices.dto;

import com.exobios.backend.devices.entity.enums.DeviceStatus;
import com.exobios.backend.devices.entity.enums.DeviceType;
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
public class DeviceDto {
    private UUID         id;
    private String       deviceId;
    private String       name;
    private DeviceType   type;
    private String       model;
    private UUID         assignedTo;
    private DeviceStatus status;
    private Integer      batteryLevel;
    private Instant      lastSyncedAt;
    private Instant      createdAt;
    private Instant      updatedAt;
}
