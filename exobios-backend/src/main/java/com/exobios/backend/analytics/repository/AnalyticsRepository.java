package com.exobios.backend.analytics.repository;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.persistence.Query;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Repository
public class AnalyticsRepository {

    @PersistenceContext
    private EntityManager em;

    public Object[] fetchDashboardCounts() {
        String sql = """
                SELECT
                    (SELECT COUNT(*) FROM users     WHERE role   = 'ASHA')       AS asha_workers,
                    (SELECT COUNT(*) FROM patients)                               AS patients,
                    (SELECT COUNT(*) FROM assessments)                            AS assessments,
                    (SELECT COUNT(*) FROM referrals)                              AS referrals,
                    (SELECT COUNT(*) FROM assessments
                         WHERE risk_level IN ('HIGH','CRITICAL'))                 AS high_critical,
                    (SELECT COUNT(*) FROM referrals  WHERE status = 'PENDING')   AS pending_referrals,
                    (SELECT COUNT(*) FROM measures)                               AS measures
                """;
        return (Object[]) em.createNativeQuery(sql).getSingleResult();
    }

    @SuppressWarnings("unchecked")
    public List<Object[]> fetchAshaPerformance(UUID ashaWorkerId, String district,
                                               Instant fromDate, Instant toDate) {
        StringBuilder sql = new StringBuilder("""
                SELECT
                    u.id,
                    u.name,
                    u.area,
                    u.district,
                    COUNT(DISTINCT p.id)                                                     AS patients_registered,
                    COUNT(DISTINCT a.id)                                                     AS assessments_completed,
                    COUNT(DISTINCT m.id)                                                     AS measures_implemented,
                    COUNT(DISTINCT r.id)                                                     AS referrals_made,
                    COUNT(DISTINCT CASE WHEN a.risk_level IN ('HIGH','CRITICAL') THEN a.id END) AS high_risk_cases
                FROM users u
                LEFT JOIN patients p    ON p.asha_worker_id = u.id
                                       AND p.created_at    BETWEEN :fromDate AND :toDate
                LEFT JOIN assessments a ON a.asha_worker_id = u.id
                                       AND a.status        != 'DRAFT'
                                       AND a.submitted_at  BETWEEN :fromDate AND :toDate
                LEFT JOIN measures m    ON m.asha_worker_id = u.id
                                       AND m.created_at    BETWEEN :fromDate AND :toDate
                LEFT JOIN referrals r   ON r.asha_worker_id = u.id
                                       AND r.created_at    BETWEEN :fromDate AND :toDate
                WHERE u.role = 'ASHA'
                """);

        Map<String, Object> params = new LinkedHashMap<>();
        params.put("fromDate", fromDate);
        params.put("toDate", toDate);

        if (district != null && !district.isBlank()) {
            sql.append(" AND u.district = :district");
            params.put("district", district);
        }
        if (ashaWorkerId != null) {
            sql.append(" AND u.id = :ashaWorkerId");
            params.put("ashaWorkerId", ashaWorkerId);
        }
        sql.append(" GROUP BY u.id, u.name, u.area, u.district ORDER BY u.name");

        Query query = em.createNativeQuery(sql.toString());
        params.forEach(query::setParameter);
        return query.getResultList();
    }

    public Object[] fetchRiskSummary(String district, String village,
                                     Instant fromDate, Instant toDate) {
        StringBuilder sql = new StringBuilder("""
                SELECT
                    COUNT(*),
                    COUNT(CASE WHEN a.risk_level = 'LOW'      THEN 1 END),
                    COUNT(CASE WHEN a.risk_level = 'MEDIUM'   THEN 1 END),
                    COUNT(CASE WHEN a.risk_level = 'HIGH'     THEN 1 END),
                    COUNT(CASE WHEN a.risk_level = 'CRITICAL' THEN 1 END)
                FROM assessments a
                JOIN patients p ON p.id = a.patient_id
                WHERE a.status      != 'DRAFT'
                  AND a.risk_level  IS NOT NULL
                  AND a.submitted_at BETWEEN :fromDate AND :toDate
                """);

        Map<String, Object> params = new LinkedHashMap<>();
        params.put("fromDate", fromDate);
        params.put("toDate", toDate);

        if (district != null && !district.isBlank()) {
            sql.append(" AND p.district = :district");
            params.put("district", district);
        }
        if (village != null && !village.isBlank()) {
            sql.append(" AND p.village = :village");
            params.put("village", village);
        }

        Query query = em.createNativeQuery(sql.toString());
        params.forEach(query::setParameter);
        return (Object[]) query.getSingleResult();
    }

    public Object[] fetchReferralSummary(String status, String priority,
                                         Instant fromDate, Instant toDate) {
        StringBuilder sql = new StringBuilder("""
                SELECT
                    COUNT(*),
                    COUNT(CASE WHEN status   = 'PENDING'   THEN 1 END),
                    COUNT(CASE WHEN status   = 'ACCEPTED'  THEN 1 END),
                    COUNT(CASE WHEN status   = 'COMPLETED' THEN 1 END),
                    COUNT(CASE WHEN status   = 'REJECTED'  THEN 1 END),
                    COUNT(CASE WHEN status   = 'CANCELLED' THEN 1 END),
                    COUNT(CASE WHEN priority = 'LOW'       THEN 1 END),
                    COUNT(CASE WHEN priority = 'MEDIUM'    THEN 1 END),
                    COUNT(CASE WHEN priority = 'HIGH'      THEN 1 END),
                    COUNT(CASE WHEN priority = 'URGENT'    THEN 1 END)
                FROM referrals
                WHERE created_at BETWEEN :fromDate AND :toDate
                """);

        Map<String, Object> params = new LinkedHashMap<>();
        params.put("fromDate", fromDate);
        params.put("toDate", toDate);

        if (status != null && !status.isBlank()) {
            sql.append(" AND status = :status");
            params.put("status", status);
        }
        if (priority != null && !priority.isBlank()) {
            sql.append(" AND priority = :priority");
            params.put("priority", priority);
        }

        Query query = em.createNativeQuery(sql.toString());
        params.forEach(query::setParameter);
        return (Object[]) query.getSingleResult();
    }

    @SuppressWarnings("unchecked")
    public List<Object[]> fetchVillageSummary(String district, Instant fromDate, Instant toDate) {
        StringBuilder sql = new StringBuilder("""
                SELECT
                    COALESCE(p.village,  'Unknown') AS village,
                    COALESCE(p.district, 'Unknown') AS district,
                    COUNT(DISTINCT p.id) AS patients,
                    COUNT(DISTINCT CASE
                        WHEN a.status != 'DRAFT'
                         AND a.submitted_at BETWEEN :fromDate AND :toDate
                        THEN a.id END) AS assessments,
                    COUNT(DISTINCT CASE
                        WHEN a.status != 'DRAFT'
                         AND a.submitted_at BETWEEN :fromDate AND :toDate
                         AND a.risk_level IN ('HIGH','CRITICAL')
                        THEN a.id END) AS high_risk_cases,
                    COUNT(DISTINCT CASE
                        WHEN r.created_at BETWEEN :fromDate AND :toDate
                        THEN r.id END)  AS referrals
                FROM patients p
                LEFT JOIN assessments a ON a.patient_id = p.id
                LEFT JOIN referrals   r ON r.patient_id = p.id
                WHERE 1=1
                """);

        Map<String, Object> params = new LinkedHashMap<>();
        params.put("fromDate", fromDate);
        params.put("toDate", toDate);

        if (district != null && !district.isBlank()) {
            sql.append(" AND p.district = :district");
            params.put("district", district);
        }

        sql.append(" GROUP BY p.village, p.district ORDER BY p.district, p.village");

        Query query = em.createNativeQuery(sql.toString());
        params.forEach(query::setParameter);
        return query.getResultList();
    }
}
