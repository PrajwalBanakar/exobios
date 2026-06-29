package com.exobios.backend.patients.repository;

import com.exobios.backend.patients.entity.Patient;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface PatientRepository extends JpaRepository<Patient, UUID> {

    // ── List queries (no search term) ────────────────────────────────────────

    /** All patients for one ASHA worker — used when no search term is provided. */
    Page<Patient> findAllByAshaWorkerId(UUID ashaWorkerId, Pageable pageable);

    // ── Search queries (non-null search term) ────────────────────────────────
    // Null search params are never passed here; service routes to the right method.
    // This avoids PostgreSQL error 42883 (undefined function for untyped null).

    /** Full-text search across name/phone/patientCode/village for one ASHA worker. */
    @Query("SELECT p FROM Patient p WHERE p.ashaWorkerId = :ashaWorkerId AND " +
           "(LOWER(p.name)        LIKE LOWER(CONCAT('%', :search, '%')) OR " +
           " LOWER(p.phone)       LIKE LOWER(CONCAT('%', :search, '%')) OR " +
           " LOWER(p.patientCode) LIKE LOWER(CONCAT('%', :search, '%')) OR " +
           " LOWER(p.village)     LIKE LOWER(CONCAT('%', :search, '%')))")
    Page<Patient> searchByAshaWorkerAndText(@Param("ashaWorkerId") UUID ashaWorkerId,
                                            @Param("search")       String search,
                                            Pageable pageable);

    /** Full-text search across name/phone/patientCode/village for all patients. */
    @Query("SELECT p FROM Patient p WHERE " +
           "LOWER(p.name)        LIKE LOWER(CONCAT('%', :search, '%')) OR " +
           "LOWER(p.phone)       LIKE LOWER(CONCAT('%', :search, '%')) OR " +
           "LOWER(p.patientCode) LIKE LOWER(CONCAT('%', :search, '%')) OR " +
           "LOWER(p.village)     LIKE LOWER(CONCAT('%', :search, '%'))")
    Page<Patient> searchByText(@Param("search") String search, Pageable pageable);

    /**
     * Returns the highest sequential number used in patient codes for a given year prefix.
     * Example call: findMaxSequenceByYearPrefix("PT-2026-%")
     * Returns 0 when no patients exist for that year yet.
     */
    @Query(value = "SELECT COALESCE(MAX(CAST(SUBSTRING(patient_code, 9) AS INTEGER)), 0) " +
                   "FROM patients WHERE patient_code LIKE :prefix",
           nativeQuery = true)
    Integer findMaxSequenceByYearPrefix(@Param("prefix") String prefix);
}
