package com.exobios.backend.devices.controller;

import com.exobios.backend.common.dto.ApiResponse;
import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.devices.dto.AssignDeviceRequest;
import com.exobios.backend.devices.dto.CreateDeviceRequest;
import com.exobios.backend.devices.dto.DeviceDto;
import com.exobios.backend.devices.dto.UpdateDeviceRequest;
import com.exobios.backend.devices.entity.enums.DeviceStatus;
import com.exobios.backend.devices.service.DeviceService;
import com.exobios.backend.security.UserPrincipal;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/devices")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ASHA', 'SUPER_ADMIN')")
@Tag(name = "Devices", description = "Medical device management — ADMIN creates/assigns; ASHA views own")
public class DeviceController {

    private final DeviceService deviceService;

    @PostMapping
    @Operation(summary = "Create a device (SUPER_ADMIN only)")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public ResponseEntity<ApiResponse<DeviceDto>> createDevice(
            @Valid @RequestBody CreateDeviceRequest request) {
        DeviceDto created = deviceService.createDevice(request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("Device created", created));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get a device by ID — ASHA: own assigned devices only; ADMIN: any")
    public ResponseEntity<ApiResponse<DeviceDto>> getDeviceById(
            @PathVariable UUID id,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(deviceService.getDeviceById(id, principal)));
    }

    @GetMapping
    @Operation(summary = "List devices — ASHA: own assigned; ADMIN: all (optional ?status filter)")
    public ResponseEntity<ApiResponse<PageResponse<DeviceDto>>> listDevices(
            @RequestParam(required = false) DeviceStatus status,
            @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC)
            Pageable pageable,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(
                deviceService.listDevices(status, pageable, principal)));
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update device details (SUPER_ADMIN only)")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public ResponseEntity<ApiResponse<DeviceDto>> updateDevice(
            @PathVariable UUID id,
            @Valid @RequestBody UpdateDeviceRequest request) {
        return ResponseEntity.ok(ApiResponse.success("Device updated",
                deviceService.updateDevice(id, request)));
    }

    @PatchMapping("/{id}/assign")
    @Operation(summary = "Assign a device to an ASHA worker (SUPER_ADMIN only)")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public ResponseEntity<ApiResponse<DeviceDto>> assignDevice(
            @PathVariable UUID id,
            @Valid @RequestBody AssignDeviceRequest request) {
        return ResponseEntity.ok(ApiResponse.success("Device assigned",
                deviceService.assignDevice(id, request)));
    }

    @PatchMapping("/{id}/unassign")
    @Operation(summary = "Unassign a device (SUPER_ADMIN only)")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public ResponseEntity<ApiResponse<DeviceDto>> unassignDevice(
            @PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success("Device unassigned",
                deviceService.unassignDevice(id)));
    }
}
