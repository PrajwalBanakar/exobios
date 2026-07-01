package com.exobios.backend.devices.entity;

import com.exobios.backend.common.entity.BaseEntity;
import com.exobios.backend.devices.entity.enums.DeviceStatus;
import com.exobios.backend.devices.entity.enums.DeviceType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "devices")
@Getter
@Setter
@NoArgsConstructor
public class Device extends BaseEntity {

    @Column(name = "device_id", unique = true, nullable = false, length = 100)
    private String deviceId;

    @Column(name = "name", nullable = false, length = 200)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(name = "type", nullable = false, length = 30)
    private DeviceType type;

    @Column(name = "model", length = 100)
    private String model;

    @Column(name = "assigned_to")
    private UUID assignedTo;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private DeviceStatus status = DeviceStatus.AVAILABLE;

    @Column(name = "battery_level")
    private Integer batteryLevel;

    @Column(name = "last_synced_at")
    private Instant lastSyncedAt;
}
