package com.exobios.backend.analytics.controller;

import com.exobios.backend.analytics.dto.DashboardDto;
import com.exobios.backend.analytics.service.AnalyticsService;
import com.exobios.backend.testsupport.AbstractControllerTest;
import com.exobios.backend.testsupport.JwtTestSupport;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(controllers = AnalyticsController.class)
class AnalyticsControllerTest extends AbstractControllerTest {

    @MockBean
    private AnalyticsService analyticsService;

    // ── Every endpoint on this controller is SUPER_ADMIN-only (class-level @PreAuthorize) ──

    @Test
    void getDashboard_withoutToken_returns401() throws Exception {
        mockMvc.perform(get("/api/v1/analytics/dashboard")).andExpect(status().isUnauthorized());
    }

    @Test
    void getDashboard_asAsha_returns403() throws Exception {
        // Analytics is explicitly SUPER_ADMIN-only — even a legitimate ASHA worker must be rejected.
        String bearer = JwtTestSupport.ashaBearer(jwtTokenProvider, UUID.randomUUID(), "9876543210");

        mockMvc.perform(get("/api/v1/analytics/dashboard").header("Authorization", bearer))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.success").value(false));
    }

    @Test
    void getDashboard_asSuperAdmin_returns200() throws Exception {
        String bearer = JwtTestSupport.adminBearer(jwtTokenProvider, UUID.randomUUID(), "9000000000");
        when(analyticsService.getDashboard()).thenReturn(
                DashboardDto.builder().totalPatients(42L).totalAshaWorkers(5L).totalAssessments(30L)
                        .totalReferrals(10L).highCriticalRiskCount(3L).pendingReferrals(2L)
                        .measuresImplemented(20L).generatedAt(Instant.now()).build());

        mockMvc.perform(get("/api/v1/analytics/dashboard").header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.totalPatients").value(42));
    }

    @Test
    void getAshaPerformance_asSuperAdmin_returns200() throws Exception {
        String bearer = JwtTestSupport.adminBearer(jwtTokenProvider, UUID.randomUUID(), "9000000000");
        when(analyticsService.getAshaPerformance(any(), any(), any(), any())).thenReturn(List.of());

        mockMvc.perform(get("/api/v1/analytics/asha-performance").header("Authorization", bearer))
                .andExpect(status().isOk());
    }

    @Test
    void getRiskSummary_asSuperAdmin_returns200() throws Exception {
        String bearer = JwtTestSupport.adminBearer(jwtTokenProvider, UUID.randomUUID(), "9000000000");
        when(analyticsService.getRiskSummary(any(), any(), any(), any())).thenReturn(
                com.exobios.backend.analytics.dto.RiskSummaryDto.builder()
                        .total(10L).low(4L).medium(3L).high(2L).critical(1L).build());

        mockMvc.perform(get("/api/v1/analytics/risk-summary").header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.total").value(10));
    }

    @Test
    void getReferralSummary_asDoctorRole_returns403() throws Exception {
        String bearer = JwtTestSupport.bearer(jwtTokenProvider, UUID.randomUUID(), "9876500000", "DOCTOR");

        mockMvc.perform(get("/api/v1/analytics/referral-summary").header("Authorization", bearer))
                .andExpect(status().isForbidden());
    }

    @Test
    void getVillageSummary_asSuperAdmin_returns200() throws Exception {
        String bearer = JwtTestSupport.adminBearer(jwtTokenProvider, UUID.randomUUID(), "9000000000");
        when(analyticsService.getVillageSummary(any(), any(), any())).thenReturn(List.of());

        mockMvc.perform(get("/api/v1/analytics/village-summary").header("Authorization", bearer))
                .andExpect(status().isOk());
    }

    @Test
    void exportAshaPerformanceCsv_asSuperAdmin_returnsCsvContentType() throws Exception {
        String bearer = JwtTestSupport.adminBearer(jwtTokenProvider, UUID.randomUUID(), "9000000000");
        when(analyticsService.exportAshaPerformanceCsv(any(), any(), any(), any()))
                .thenReturn("ASHA Worker ID,Name\n");

        mockMvc.perform(get("/api/v1/analytics/export/asha-performance.csv").header("Authorization", bearer))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith("text/csv"));
    }

    @Test
    void exportAshaPerformanceCsv_withoutToken_returns401() throws Exception {
        mockMvc.perform(get("/api/v1/analytics/export/asha-performance.csv"))
                .andExpect(status().isUnauthorized());
    }
}
