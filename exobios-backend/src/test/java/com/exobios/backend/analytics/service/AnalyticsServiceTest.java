package com.exobios.backend.analytics.service;

import com.exobios.backend.analytics.dto.AshaPerformanceDto;
import com.exobios.backend.analytics.dto.DashboardDto;
import com.exobios.backend.analytics.dto.RiskSummaryDto;
import com.exobios.backend.analytics.repository.AnalyticsRepository;
import com.exobios.backend.common.exception.BadRequestException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AnalyticsServiceTest {

    @Mock private AnalyticsRepository analyticsRepository;

    private AnalyticsService analyticsService;

    @BeforeEach
    void setUp() {
        analyticsService = new AnalyticsService(analyticsRepository);
    }

    // ── getDashboard — row-array mapping ─────────────────────────────────────────

    @Test
    void getDashboard_mapsRawRowIntoNamedFields() {
        Object[] row = {5L, 42L, 30L, 10L, 3L, 2L, 20L};
        when(analyticsRepository.fetchDashboardCounts()).thenReturn(row);

        DashboardDto result = analyticsService.getDashboard();

        assertThat(result.getTotalAshaWorkers()).isEqualTo(5L);
        assertThat(result.getTotalPatients()).isEqualTo(42L);
        assertThat(result.getTotalAssessments()).isEqualTo(30L);
        assertThat(result.getTotalReferrals()).isEqualTo(10L);
        assertThat(result.getHighCriticalRiskCount()).isEqualTo(3L);
        assertThat(result.getPendingReferrals()).isEqualTo(2L);
        assertThat(result.getMeasuresImplemented()).isEqualTo(20L);
        assertThat(result.getGeneratedAt()).isNotNull();
    }

    @Test
    void getDashboard_treatsNullCellsAsZero() {
        Object[] row = {null, null, null, null, null, null, null};
        when(analyticsRepository.fetchDashboardCounts()).thenReturn(row);

        DashboardDto result = analyticsService.getDashboard();

        assertThat(result.getTotalPatients()).isZero();
        assertThat(result.getHighCriticalRiskCount()).isZero();
    }

    // ── getAshaPerformance — row-list mapping + UUID coercion ───────────────────

    @Test
    void getAshaPerformance_mapsEachRowAndCoercesUuidColumn() {
        UUID ashaId = UUID.randomUUID();
        Object[] row = {ashaId, "Sunita Devi", "Rampur", "Rampur District", 12L, 8L, 5L, 2L, 1L};
        when(analyticsRepository.fetchAshaPerformance(any(), any(), any(), any())).thenReturn(List.<Object[]>of(row));

        List<AshaPerformanceDto> result = analyticsService.getAshaPerformance(null, null, null, null);

        assertThat(result).hasSize(1);
        assertThat(result.get(0).getAshaWorkerId()).isEqualTo(ashaId);
        assertThat(result.get(0).getAshaName()).isEqualTo("Sunita Devi");
        assertThat(result.get(0).getHighRiskCases()).isEqualTo(1L);
    }

    @Test
    void getAshaPerformance_withNoDateRange_defaultsToStartOfMonthThroughNow() {
        when(analyticsRepository.fetchAshaPerformance(any(), any(), any(), any())).thenReturn(List.of());

        analyticsService.getAshaPerformance(null, null, null, null);

        var captor = org.mockito.ArgumentCaptor.forClass(Instant.class);
        org.mockito.Mockito.verify(analyticsRepository)
                .fetchAshaPerformance(eq((UUID) null), eq((String) null), captor.capture(), any());
        assertThat(captor.getValue()).isBefore(Instant.now());
    }

    // ── resolveRange — validation ────────────────────────────────────────────────

    @Test
    void getRiskSummary_withFromDateAfterToDate_throwsBadRequest() {
        Instant now = Instant.now();
        Instant from = now;
        Instant to   = now.minus(1, ChronoUnit.DAYS);

        assertThatThrownBy(() -> analyticsService.getRiskSummary(null, null, from, to))
                .isInstanceOf(BadRequestException.class);
    }

    @Test
    void getRiskSummary_mapsRowIntoDto() {
        Object[] row = {10L, 4L, 3L, 2L, 1L};
        when(analyticsRepository.fetchRiskSummary(any(), any(), any(), any())).thenReturn(row);

        RiskSummaryDto result = analyticsService.getRiskSummary(null, null, null, null);

        assertThat(result.getTotal()).isEqualTo(10L);
        assertThat(result.getCritical()).isEqualTo(1L);
    }

    // ── exportAshaPerformanceCsv — header + escaping ────────────────────────────

    @Test
    void exportAshaPerformanceCsv_includesHeaderRow() {
        when(analyticsRepository.fetchAshaPerformance(any(), any(), any(), any())).thenReturn(List.of());

        String csv = analyticsService.exportAshaPerformanceCsv(null, null, null, null);

        assertThat(csv).startsWith("ASHA Worker ID,Name,Area,District,Patients Registered,");
    }

    @Test
    void exportAshaPerformanceCsv_escapesFieldsContainingCommas() {
        UUID ashaId = UUID.randomUUID();
        Object[] row = {ashaId, "Devi, Sunita", "Rampur, Block A", "Rampur", 1L, 1L, 1L, 0L, 0L};
        when(analyticsRepository.fetchAshaPerformance(any(), any(), any(), any())).thenReturn(List.<Object[]>of(row));

        String csv = analyticsService.exportAshaPerformanceCsv(null, null, null, null);

        assertThat(csv).contains("\"Devi, Sunita\"").contains("\"Rampur, Block A\"");
    }
}
