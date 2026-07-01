package com.exobios.backend.devices.repository;

import com.exobios.backend.devices.entity.Device;
import com.exobios.backend.devices.entity.enums.DeviceStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface DeviceRepository extends JpaRepository<Device, UUID> {

    boolean existsByDeviceId(String deviceId);

    Optional<Device> findByDeviceId(String deviceId);

    Page<Device> findAllByAssignedTo(UUID assignedTo, Pageable pageable);

    Page<Device> findAllByStatus(DeviceStatus status, Pageable pageable);
}
