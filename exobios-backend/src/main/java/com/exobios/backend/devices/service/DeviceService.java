package com.exobios.backend.devices.service;

import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.common.exception.BadRequestException;
import com.exobios.backend.common.exception.ConflictException;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.devices.dto.AssignDeviceRequest;
import com.exobios.backend.devices.dto.CreateDeviceRequest;
import com.exobios.backend.devices.dto.DeviceDto;
import com.exobios.backend.devices.dto.UpdateDeviceRequest;
import com.exobios.backend.devices.entity.Device;
import com.exobios.backend.devices.entity.enums.DeviceStatus;
import com.exobios.backend.devices.exception.DeviceNotFoundException;
import com.exobios.backend.devices.mapper.DeviceMapper;
import com.exobios.backend.common.exception.ResourceNotFoundException;
import com.exobios.backend.devices.repository.DeviceRepository;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.users.entity.enums.Role;
import com.exobios.backend.users.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.exobios.backend.audit.annotation.Auditable;
import com.exobios.backend.audit.entity.enums.AuditAction;
import java.util.UUID;

@Slf4j
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class DeviceService {

    private final DeviceRepository deviceRepository;
    private final DeviceMapper     deviceMapper;
    private final UserRepository   userRepository;

    @Auditable(action = AuditAction.CREATE, entityType = "DEVICE")
    @Transactional
    public DeviceDto createDevice(CreateDeviceRequest request) {
        if (deviceRepository.existsByDeviceId(request.getDeviceId())) {
            throw new ConflictException("Device with deviceId '" + request.getDeviceId() + "' already exists");
        }
        Device device = new Device();
        device.setDeviceId(request.getDeviceId());
        device.setName(request.getName());
        device.setType(request.getType());
        device.setModel(request.getModel());
        device.setStatus(DeviceStatus.AVAILABLE);

        Device saved = deviceRepository.save(device);
        log.info("Device created id={} deviceId={}", saved.getId(), saved.getDeviceId());
        return deviceMapper.toDto(saved);
    }

    public DeviceDto getDeviceById(UUID id, UserPrincipal principal) {
        Device device = findOrThrow(id);
        assertReadAccess(device, principal);
        return deviceMapper.toDto(device);
    }

    public PageResponse<DeviceDto> listDevices(DeviceStatus status, Pageable pageable,
                                                UserPrincipal principal) {
        Page<Device> page;
        if (isAsha(principal)) {
            page = deviceRepository.findAllByAssignedTo(principal.getId(), pageable);
        } else {
            page = status != null
                    ? deviceRepository.findAllByStatus(status, pageable)
                    : deviceRepository.findAll(pageable);
        }
        return PageResponse.of(page.map(deviceMapper::toDto));
    }

    @Auditable(action = AuditAction.UPDATE, entityType = "DEVICE")
    @Transactional
    public DeviceDto updateDevice(UUID id, UpdateDeviceRequest request) {
        Device device = findOrThrow(id);

        if (StringUtils.hasText(request.getName()))  device.setName(request.getName());
        if (StringUtils.hasText(request.getModel())) device.setModel(request.getModel());
        if (request.getStatus()       != null) device.setStatus(request.getStatus());
        if (request.getBatteryLevel() != null) device.setBatteryLevel(request.getBatteryLevel());
        if (request.getLastSyncedAt() != null) device.setLastSyncedAt(request.getLastSyncedAt());

        return deviceMapper.toDto(deviceRepository.save(device));
    }

    @Auditable(action = AuditAction.STATUS_CHANGE, entityType = "DEVICE")
    @Transactional
    public DeviceDto assignDevice(UUID id, AssignDeviceRequest request) {
        Device device = findOrThrow(id);
        if (device.getStatus() == DeviceStatus.RETIRED) {
            throw new BadRequestException("Cannot assign a RETIRED device");
        }
        if (device.getStatus() == DeviceStatus.MAINTENANCE) {
            throw new BadRequestException("Cannot assign a device that is under MAINTENANCE");
        }
        if (!userRepository.existsById(request.getAssignedTo())) {
            throw new ResourceNotFoundException("User", request.getAssignedTo());
        }
        device.setAssignedTo(request.getAssignedTo());
        device.setStatus(DeviceStatus.ASSIGNED);
        log.info("Device id={} assigned to user={}", id, request.getAssignedTo());
        return deviceMapper.toDto(deviceRepository.save(device));
    }

    @Auditable(action = AuditAction.STATUS_CHANGE, entityType = "DEVICE")
    @Transactional
    public DeviceDto unassignDevice(UUID id) {
        Device device = findOrThrow(id);
        if (device.getAssignedTo() == null) {
            throw new BadRequestException("Device is not currently assigned");
        }
        UUID previousOwner = device.getAssignedTo();
        device.setAssignedTo(null);
        device.setStatus(DeviceStatus.AVAILABLE);
        log.info("Device id={} unassigned from user={}", id, previousOwner);
        return deviceMapper.toDto(deviceRepository.save(device));
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private Device findOrThrow(UUID id) {
        return deviceRepository.findById(id).orElseThrow(() -> new DeviceNotFoundException(id));
    }

    private void assertReadAccess(Device device, UserPrincipal principal) {
        if (isAsha(principal)) {
            if (!principal.getId().equals(device.getAssignedTo())) {
                throw new ForbiddenException("Access denied: this device is not assigned to you");
            }
        }
    }

    private boolean isAsha(UserPrincipal principal) {
        return Role.ASHA.name().equals(principal.getRole());
    }
}
