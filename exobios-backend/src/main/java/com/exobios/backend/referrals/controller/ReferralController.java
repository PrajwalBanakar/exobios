package com.exobios.backend.referrals.controller;

import com.exobios.backend.common.dto.ApiResponse;
import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.referrals.dto.CreateReferralRequest;
import com.exobios.backend.referrals.dto.ReferralDto;
import com.exobios.backend.referrals.dto.ReferralStatusUpdateRequest;
import com.exobios.backend.referrals.dto.UpdateReferralRequest;
import com.exobios.backend.referrals.entity.enums.ReferralStatus;
import com.exobios.backend.referrals.service.ReferralService;
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
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ASHA', 'SUPER_ADMIN')")
@Tag(name = "Referrals", description = "Patient referrals to higher medical facilities")
public class ReferralController {

    private final ReferralService referralService;

    @PostMapping("/referrals")
    @Operation(summary = "Create a referral (assessment must be submitted first)")
    public ResponseEntity<ApiResponse<ReferralDto>> createReferral(
            @Valid @RequestBody CreateReferralRequest request,
            @AuthenticationPrincipal UserPrincipal principal) {
        ReferralDto created = referralService.createReferral(request, principal);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("Referral created successfully", created));
    }

    @GetMapping("/referrals/{id}")
    @Operation(summary = "Get a referral by ID")
    public ResponseEntity<ApiResponse<ReferralDto>> getReferralById(
            @PathVariable UUID id,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(referralService.getReferralById(id, principal)));
    }

    @GetMapping("/referrals")
    @Operation(summary = "List/search referrals — optional filters: patientId, status")
    public ResponseEntity<ApiResponse<PageResponse<ReferralDto>>> getReferrals(
            @RequestParam(required = false) UUID patientId,
            @RequestParam(required = false) ReferralStatus status,
            @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC)
            Pageable pageable,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(
                referralService.getReferrals(patientId, status, pageable, principal)));
    }

    @GetMapping("/assessments/{assessmentId}/referrals")
    @Operation(summary = "Get all referrals for an assessment")
    public ResponseEntity<ApiResponse<List<ReferralDto>>> getAssessmentReferrals(
            @PathVariable UUID assessmentId,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(
                referralService.getAssessmentReferrals(assessmentId, principal)));
    }

    @GetMapping("/patients/{patientId}/referrals")
    @Operation(summary = "Get referral history for a patient")
    public ResponseEntity<ApiResponse<PageResponse<ReferralDto>>> getPatientReferrals(
            @PathVariable UUID patientId,
            @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC)
            Pageable pageable,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(
                referralService.getPatientReferrals(patientId, pageable, principal)));
    }

    @PutMapping("/referrals/{id}")
    @Operation(summary = "Update a referral (PENDING or ACCEPTED only)")
    public ResponseEntity<ApiResponse<ReferralDto>> updateReferral(
            @PathVariable UUID id,
            @Valid @RequestBody UpdateReferralRequest request,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success("Referral updated successfully",
                referralService.updateReferral(id, request, principal)));
    }

    @PatchMapping("/referrals/{id}/status")
    @Operation(summary = "Update referral status")
    public ResponseEntity<ApiResponse<ReferralDto>> updateStatus(
            @PathVariable UUID id,
            @Valid @RequestBody ReferralStatusUpdateRequest request,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success("Referral status updated",
                referralService.updateStatus(id, request.getStatus(), principal)));
    }

    @DeleteMapping("/referrals/{id}")
    @Operation(summary = "Cancel/delete a referral (PENDING or ACCEPTED only)")
    public ResponseEntity<ApiResponse<Void>> deleteReferral(
            @PathVariable UUID id,
            @AuthenticationPrincipal UserPrincipal principal) {
        referralService.deleteReferral(id, principal);
        return ResponseEntity.ok(ApiResponse.success("Referral deleted successfully", null));
    }
}
