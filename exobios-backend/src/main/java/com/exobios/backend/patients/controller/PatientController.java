package com.exobios.backend.patients.controller;

import com.exobios.backend.common.dto.ApiResponse;
import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.patients.dto.ChangePatientStatusRequest;
import com.exobios.backend.patients.dto.CreatePatientRequest;
import com.exobios.backend.patients.dto.PatientDto;
import com.exobios.backend.patients.dto.UpdatePatientRequest;
import com.exobios.backend.patients.service.PatientService;
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
@RequestMapping("/api/v1/patients")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ASHA', 'SUPER_ADMIN')")
@Tag(name = "Patients", description = "Patient management — ASHA manages own patients; SUPER_ADMIN manages all")
public class PatientController {

    private final PatientService patientService;

    @GetMapping
    @Operation(summary = "List patients with optional search — ASHA sees own patients only; SUPER_ADMIN sees all")
    public ResponseEntity<ApiResponse<PageResponse<PatientDto>>> getAllPatients(
            @RequestParam(required = false) String search,
            @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC)
            Pageable pageable,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(
                patientService.getAllPatients(search, pageable, principal)));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get a patient by ID — ASHA can only access own patients")
    public ResponseEntity<ApiResponse<PatientDto>> getPatientById(
            @PathVariable UUID id,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(
                patientService.getPatientById(id, principal)));
    }

    @PostMapping
    @Operation(summary = "Create a patient — ASHA creates under self; SUPER_ADMIN must provide ashaWorkerId")
    public ResponseEntity<ApiResponse<PatientDto>> createPatient(
            @Valid @RequestBody CreatePatientRequest request,
            @AuthenticationPrincipal UserPrincipal principal) {
        PatientDto created = patientService.createPatient(request, principal);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("Patient created successfully", created));
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a patient — ASHA can only update own patients")
    public ResponseEntity<ApiResponse<PatientDto>> updatePatient(
            @PathVariable UUID id,
            @Valid @RequestBody UpdatePatientRequest request,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success("Patient updated successfully",
                patientService.updatePatient(id, request, principal)));
    }

    @PatchMapping("/{id}/status")
    @Operation(summary = "Change patient status: ACTIVE | INACTIVE | DECEASED")
    public ResponseEntity<ApiResponse<PatientDto>> changeStatus(
            @PathVariable UUID id,
            @Valid @RequestBody ChangePatientStatusRequest request,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success("Status updated successfully",
                patientService.changeStatus(id, request.getStatus(), principal)));
    }
}
