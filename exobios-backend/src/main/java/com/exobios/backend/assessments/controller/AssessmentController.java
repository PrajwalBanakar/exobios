package com.exobios.backend.assessments.controller;

import com.exobios.backend.assessments.dto.AssessmentDto;
import com.exobios.backend.assessments.dto.CreateAssessmentRequest;
import com.exobios.backend.assessments.dto.UpdateAssessmentRequest;
import com.exobios.backend.assessments.service.AssessmentService;
import com.exobios.backend.common.dto.ApiResponse;
import com.exobios.backend.common.dto.PageResponse;
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
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ASHA', 'SUPER_ADMIN')")
@Tag(name = "Assessments", description = "Clinical assessments — ASHA manages own; SUPER_ADMIN views all")
public class AssessmentController {

    private final AssessmentService assessmentService;

    @PostMapping("/assessments")
    @Operation(summary = "Create a new assessment (DRAFT)")
    public ResponseEntity<ApiResponse<AssessmentDto>> createAssessment(
            @Valid @RequestBody CreateAssessmentRequest request,
            @AuthenticationPrincipal UserPrincipal principal) {
        AssessmentDto created = assessmentService.createAssessment(request, principal);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("Assessment created successfully", created));
    }

    @GetMapping("/assessments/{id}")
    @Operation(summary = "Get assessment detail by ID")
    public ResponseEntity<ApiResponse<AssessmentDto>> getAssessmentById(
            @PathVariable UUID id,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(
                assessmentService.getAssessmentById(id, principal)));
    }

    @GetMapping("/patients/{patientId}/assessments")
    @Operation(summary = "Get assessment history for a patient")
    public ResponseEntity<ApiResponse<PageResponse<AssessmentDto>>> getPatientAssessments(
            @PathVariable UUID patientId,
            @PageableDefault(size = 20, sort = "assessedAt", direction = Sort.Direction.DESC)
            Pageable pageable,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(
                assessmentService.getPatientAssessments(patientId, pageable, principal)));
    }

    @PutMapping("/assessments/{id}")
    @Operation(summary = "Update a DRAFT assessment")
    public ResponseEntity<ApiResponse<AssessmentDto>> updateAssessment(
            @PathVariable UUID id,
            @Valid @RequestBody UpdateAssessmentRequest request,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success("Assessment updated successfully",
                assessmentService.updateAssessment(id, request, principal)));
    }

    @PatchMapping("/assessments/{id}/submit")
    @Operation(summary = "Submit an assessment (DRAFT → SUBMITTED)")
    public ResponseEntity<ApiResponse<AssessmentDto>> submitAssessment(
            @PathVariable UUID id,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success("Assessment submitted successfully",
                assessmentService.submitAssessment(id, principal)));
    }
}
