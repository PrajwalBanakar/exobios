package com.exobios.backend.analytics.service;

import com.exobios.backend.analytics.dto.AshaPerformanceDto;
import com.exobios.backend.analytics.dto.DashboardDto;
import com.exobios.backend.analytics.dto.ReferralSummaryDto;
import com.exobios.backend.analytics.dto.RiskSummaryDto;
import com.exobios.backend.analytics.dto.VillageSummaryDto;
import com.exobios.backend.analytics.repository.AnalyticsRepository;
import com.exobios.backend.common.exception.BadRequestException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.StringWriter;
import java.time.Instant;
import java.time.YearMonth;
import java.time.ZoneOffset;
import java.util.List;
import java.util.UUID;

@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class AnalyticsService {

    private final AnalyticsRepository analyticsRepository;

    // ── Dashboard ─────────────────────────────────────────────────────────────

    public DashboardDto getDashboard() {
        Object[] row = analyticsRepository.fetchDashboardCounts();
        return DashboardDto.builder()
                .totalAshaWorkers(toLong(row[0]))
                .totalPatients(toLong(row[1]))
                .totalAssessments(toLong(row[2]))
                .totalReferrals(toLong(row[3]))
                .highCriticalRiskCount(toLong(row[4]))
                .pendingReferrals(toLong(row[5]))
                .measuresImplemented(toLong(row[6]))
                .generatedAt(Instant.now())
                .build();
    }

    // ── ASHA Performance ─────────────────────────────────────────────────────

    public List<AshaPerformanceDto> getAshaPerformance(UUID ashaWorkerId, String district,
                                                        Instant fromDate, Instant toDate) {
        Instant[] range = resolveRange(fromDate, toDate);
        return analyticsRepository
                .fetchAshaPerformance(ashaWorkerId, district, range[0], range[1])
                .stream()
                .map(row -> AshaPerformanceDto.builder()
                        .ashaWorkerId(toUuid(row[0]))
                        .ashaName((String) row[1])
                        .area((String) row[2])
                        .district((String) row[3])
                        .patientsRegistered(toLong(row[4]))
                        .assessmentsCompleted(toLong(row[5]))
                        .measuresImplemented(toLong(row[6]))
                        .referralsMade(toLong(row[7]))
                        .highRiskCases(toLong(row[8]))
                        .build())
                .toList();
    }

    // ── Risk Summary ──────────────────────────────────────────────────────────

    public RiskSummaryDto getRiskSummary(String district, String village,
                                         Instant fromDate, Instant toDate) {
        Instant[] range = resolveRange(fromDate, toDate);
        Object[] row = analyticsRepository.fetchRiskSummary(district, village, range[0], range[1]);
        return RiskSummaryDto.builder()
                .total(toLong(row[0]))
                .low(toLong(row[1]))
                .medium(toLong(row[2]))
                .high(toLong(row[3]))
                .critical(toLong(row[4]))
                .fromDate(range[0])
                .toDate(range[1])
                .build();
    }

    // ── Referral Summary ──────────────────────────────────────────────────────

    public ReferralSummaryDto getReferralSummary(String status, String priority,
                                                  Instant fromDate, Instant toDate) {
        Instant[] range = resolveRange(fromDate, toDate);
        Object[] row = analyticsRepository.fetchReferralSummary(status, priority, range[0], range[1]);
        return ReferralSummaryDto.builder()
                .total(toLong(row[0]))
                .pending(toLong(row[1]))
                .accepted(toLong(row[2]))
                .completed(toLong(row[3]))
                .rejected(toLong(row[4]))
                .cancelled(toLong(row[5]))
                .priorityLow(toLong(row[6]))
                .priorityMedium(toLong(row[7]))
                .priorityHigh(toLong(row[8]))
                .priorityUrgent(toLong(row[9]))
                .fromDate(range[0])
                .toDate(range[1])
                .build();
    }

    // ── Village Summary ───────────────────────────────────────────────────────

    public List<VillageSummaryDto> getVillageSummary(String district,
                                                      Instant fromDate, Instant toDate) {
        Instant[] range = resolveRange(fromDate, toDate);
        return analyticsRepository
                .fetchVillageSummary(district, range[0], range[1])
                .stream()
                .map(row -> VillageSummaryDto.builder()
                        .village((String) row[0])
                        .district((String) row[1])
                        .patients(toLong(row[2]))
                        .assessments(toLong(row[3]))
                        .highRiskCases(toLong(row[4]))
                        .referrals(toLong(row[5]))
                        .build())
                .toList();
    }

    // ── CSV Export ────────────────────────────────────────────────────────────

    public String exportAshaPerformanceCsv(UUID ashaWorkerId, String district,
                                            Instant fromDate, Instant toDate) {
        List<AshaPerformanceDto> data = getAshaPerformance(ashaWorkerId, district, fromDate, toDate);
        StringWriter sw = new StringWriter(256);
        sw.write("ASHA Worker ID,Name,Area,District,Patients Registered,"
                + "Assessments Completed,Measures Implemented,Referrals Made,High Risk Cases\n");
        for (AshaPerformanceDto dto : data) {
            sw.write(String.join(",",
                    dto.getAshaWorkerId().toString(),
                    escapeCsv(dto.getAshaName()),
                    escapeCsv(dto.getArea()),
                    escapeCsv(dto.getDistrict()),
                    String.valueOf(dto.getPatientsRegistered()),
                    String.valueOf(dto.getAssessmentsCompleted()),
                    String.valueOf(dto.getMeasuresImplemented()),
                    String.valueOf(dto.getReferralsMade()),
                    String.valueOf(dto.getHighRiskCases())));
            sw.write('\n');
        }
        return sw.toString();
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private Instant[] resolveRange(Instant from, Instant to) {
        if (from == null) {
            from = YearMonth.now(ZoneOffset.UTC).atDay(1)
                    .atStartOfDay(ZoneOffset.UTC).toInstant();
        }
        if (to == null) {
            to = Instant.now();
        }
        if (from.isAfter(to)) {
            throw new BadRequestException("fromDate must not be after toDate");
        }
        return new Instant[]{from, to};
    }

    private long toLong(Object value) {
        if (value == null) return 0L;
        return ((Number) value).longValue();
    }

    private UUID toUuid(Object value) {
        if (value == null) return null;
        if (value instanceof UUID) return (UUID) value;
        return UUID.fromString(value.toString());
    }

    private String escapeCsv(String value) {
        if (value == null) return "";
        if (value.contains(",") || value.contains("\"") || value.contains("\n")) {
            return "\"" + value.replace("\"", "\"\"") + "\"";
        }
        return value;
    }
}
