package com.exobios.backend.analytics.controller;

import com.exobios.backend.analytics.dto.AshaPerformanceDto;
import com.exobios.backend.analytics.dto.DashboardDto;
import com.exobios.backend.analytics.dto.ReferralSummaryDto;
import com.exobios.backend.analytics.dto.RiskSummaryDto;
import com.exobios.backend.analytics.dto.VillageSummaryDto;
import com.exobios.backend.analytics.service.AnalyticsService;
import com.exobios.backend.common.dto.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/analytics")
@RequiredArgsConstructor
@PreAuthorize("hasRole('SUPER_ADMIN')")
@Tag(name = "Analytics", description = "Reports and analytics — SUPER_ADMIN only")
public class AnalyticsController {

    private final AnalyticsService analyticsService;

    @GetMapping("/dashboard")
    @Operation(summary = "Overall platform counts: patients, ASHA workers, assessments, referrals, risk")
    public ResponseEntity<ApiResponse<DashboardDto>> getDashboard() {
        return ResponseEntity.ok(ApiResponse.success(analyticsService.getDashboard()));
    }

    @GetMapping("/asha-performance")
    @Operation(summary = "Per-ASHA performance: patients registered, assessments, measures, referrals, high-risk cases")
    public ResponseEntity<ApiResponse<List<AshaPerformanceDto>>> getAshaPerformance(
            @RequestParam(required = false) UUID    ashaWorkerId,
            @RequestParam(required = false) String  district,
            @RequestParam(required = false) Instant fromDate,
            @RequestParam(required = false) Instant toDate) {
        return ResponseEntity.ok(ApiResponse.success(
                analyticsService.getAshaPerformance(ashaWorkerId, district, fromDate, toDate)));
    }

    @GetMapping("/risk-summary")
    @Operation(summary = "Risk level distribution (LOW/MEDIUM/HIGH/CRITICAL) for submitted assessments")
    public ResponseEntity<ApiResponse<RiskSummaryDto>> getRiskSummary(
            @RequestParam(required = false) String  district,
            @RequestParam(required = false) String  village,
            @RequestParam(required = false) Instant fromDate,
            @RequestParam(required = false) Instant toDate) {
        return ResponseEntity.ok(ApiResponse.success(
                analyticsService.getRiskSummary(district, village, fromDate, toDate)));
    }

    @GetMapping("/referral-summary")
    @Operation(summary = "Referral counts by status and priority within a date range")
    public ResponseEntity<ApiResponse<ReferralSummaryDto>> getReferralSummary(
            @RequestParam(required = false) String  status,
            @RequestParam(required = false) String  priority,
            @RequestParam(required = false) Instant fromDate,
            @RequestParam(required = false) Instant toDate) {
        return ResponseEntity.ok(ApiResponse.success(
                analyticsService.getReferralSummary(status, priority, fromDate, toDate)));
    }

    @GetMapping("/village-summary")
    @Operation(summary = "Village-wise patient, assessment, high-risk, and referral counts")
    public ResponseEntity<ApiResponse<List<VillageSummaryDto>>> getVillageSummary(
            @RequestParam(required = false) String  district,
            @RequestParam(required = false) Instant fromDate,
            @RequestParam(required = false) Instant toDate) {
        return ResponseEntity.ok(ApiResponse.success(
                analyticsService.getVillageSummary(district, fromDate, toDate)));
    }

    @GetMapping("/export/asha-performance.csv")
    @Operation(summary = "Download ASHA performance report as CSV")
    public ResponseEntity<String> exportAshaPerformanceCsv(
            @RequestParam(required = false) UUID    ashaWorkerId,
            @RequestParam(required = false) String  district,
            @RequestParam(required = false) Instant fromDate,
            @RequestParam(required = false) Instant toDate) {
        String csv = analyticsService.exportAshaPerformanceCsv(ashaWorkerId, district, fromDate, toDate);
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"asha-performance.csv\"")
                .contentType(MediaType.parseMediaType("text/csv;charset=UTF-8"))
                .body(csv);
    }
}
