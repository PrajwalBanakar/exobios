package com.exobios.backend.sos.controller;

import com.exobios.backend.common.dto.ApiResponse;
import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.sos.dto.CreateSosRequest;
import com.exobios.backend.sos.dto.SosRecordDto;
import com.exobios.backend.sos.dto.UpdateSosStatusRequest;
import com.exobios.backend.sos.entity.enums.SosStatus;
import com.exobios.backend.sos.service.SosService;
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
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/sos")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ASHA', 'SUPER_ADMIN')")
@Tag(name = "SOS / Emergency", description = "Emergency SOS records created by ASHA workers")
public class SosController {

    private final SosService sosService;

    @PostMapping
    @Operation(summary = "Create an SOS record (ASHA only)")
    @PreAuthorize("hasRole('ASHA')")
    public ResponseEntity<ApiResponse<SosRecordDto>> createSos(
            @Valid @RequestBody CreateSosRequest request,
            @AuthenticationPrincipal UserPrincipal principal) {
        SosRecordDto created = sosService.createSos(request, principal);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("SOS record created", created));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get an SOS record by ID")
    public ResponseEntity<ApiResponse<SosRecordDto>> getSosById(
            @PathVariable UUID id,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(sosService.getSosById(id, principal)));
    }

    @GetMapping
    @Operation(summary = "List SOS records — ASHA sees own; ADMIN sees all. Optional ?status filter")
    public ResponseEntity<ApiResponse<PageResponse<SosRecordDto>>> listSosRecords(
            @RequestParam(required = false) SosStatus status,
            @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC)
            Pageable pageable,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(
                sosService.listSosRecords(status, pageable, principal)));
    }

    @PatchMapping("/{id}/status")
    @Operation(summary = "Update SOS status — ADMIN: any status; ASHA: cancel own ACTIVE record only")
    public ResponseEntity<ApiResponse<SosRecordDto>> updateSosStatus(
            @PathVariable UUID id,
            @Valid @RequestBody UpdateSosStatusRequest request,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success("SOS status updated",
                sosService.updateSosStatus(id, request.getStatus(), principal)));
    }
}
