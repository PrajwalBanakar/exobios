package com.exobios.backend.doctor.controller;

import com.exobios.backend.common.dto.ApiResponse;
import com.exobios.backend.doctor.dto.DoctorDashboardDto;
import com.exobios.backend.doctor.service.DoctorService;
import com.exobios.backend.security.UserPrincipal;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('DOCTOR', 'SUPER_ADMIN')")
@Tag(name = "Doctor", description = "Doctor dashboard and referral-review summary")
public class DoctorController {

    private final DoctorService doctorService;

    @GetMapping("/doctor/dashboard")
    @Operation(summary = "Doctor dashboard — referral counts by review stage for the calling doctor")
    public ResponseEntity<ApiResponse<DoctorDashboardDto>> getDashboard(
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(doctorService.getDashboard(principal)));
    }
}
