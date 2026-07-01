package com.exobios.backend.measures.controller;

import com.exobios.backend.common.dto.ApiResponse;
import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.measures.dto.CreateMeasureRequest;
import com.exobios.backend.measures.dto.MeasureDto;
import com.exobios.backend.measures.dto.UpdateMeasureRequest;
import com.exobios.backend.measures.service.MeasureService;
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
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ASHA', 'SUPER_ADMIN')")
@Tag(name = "Measures", description = "Clinical measures taken after AI recommendations")
public class MeasureController {

    private final MeasureService measureService;

    @PostMapping("/measures")
    @Operation(summary = "Record a clinical measure for an assessment")
    public ResponseEntity<ApiResponse<MeasureDto>> createMeasure(
            @Valid @RequestBody CreateMeasureRequest request,
            @AuthenticationPrincipal UserPrincipal principal) {
        MeasureDto created = measureService.createMeasure(request, principal);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("Measure recorded successfully", created));
    }

    @GetMapping("/measures/{id}")
    @Operation(summary = "Get a measure by ID")
    public ResponseEntity<ApiResponse<MeasureDto>> getMeasureById(
            @PathVariable UUID id,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(measureService.getMeasureById(id, principal)));
    }

    @GetMapping("/measures")
    @Operation(summary = "List all measures — ASHA sees own; SUPER_ADMIN sees all")
    public ResponseEntity<ApiResponse<PageResponse<MeasureDto>>> getAllMeasures(
            @PageableDefault(size = 20, sort = "implementedAt", direction = Sort.Direction.DESC)
            Pageable pageable,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(measureService.getAllMeasures(pageable, principal)));
    }

    @GetMapping("/assessments/{assessmentId}/measures")
    @Operation(summary = "Get assessment timeline — all measures for an assessment in chronological order")
    public ResponseEntity<ApiResponse<List<MeasureDto>>> getAssessmentTimeline(
            @PathVariable UUID assessmentId,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(
                measureService.getAssessmentTimeline(assessmentId, principal)));
    }

    @PutMapping("/measures/{id}")
    @Operation(summary = "Update a measure")
    public ResponseEntity<ApiResponse<MeasureDto>> updateMeasure(
            @PathVariable UUID id,
            @Valid @RequestBody UpdateMeasureRequest request,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success("Measure updated successfully",
                measureService.updateMeasure(id, request, principal)));
    }

    @DeleteMapping("/measures/{id}")
    @Operation(summary = "Delete a measure")
    public ResponseEntity<ApiResponse<Void>> deleteMeasure(
            @PathVariable UUID id,
            @AuthenticationPrincipal UserPrincipal principal) {
        measureService.deleteMeasure(id, principal);
        return ResponseEntity.ok(ApiResponse.success("Measure deleted successfully", null));
    }
}
