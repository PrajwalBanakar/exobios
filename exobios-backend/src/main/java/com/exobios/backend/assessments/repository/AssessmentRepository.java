package com.exobios.backend.assessments.repository;

import com.exobios.backend.assessments.entity.Assessment;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface AssessmentRepository extends JpaRepository<Assessment, UUID> {

    Page<Assessment> findAllByPatientId(UUID patientId, Pageable pageable);

    Page<Assessment> findAllByAshaWorkerId(UUID ashaWorkerId, Pageable pageable);

    Page<Assessment> findAllByPatientIdAndAshaWorkerId(UUID patientId, UUID ashaWorkerId, Pageable pageable);

    @Query(value = "SELECT COALESCE(MAX(CAST(SUBSTRING(assessment_number, 11) AS INTEGER)), 0) " +
                   "FROM assessments WHERE assessment_number LIKE :prefix",
           nativeQuery = true)
    Integer findMaxSequenceByYearPrefix(@Param("prefix") String prefix);
}
