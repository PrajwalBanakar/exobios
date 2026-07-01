package com.exobios.backend.measures.repository;

import com.exobios.backend.measures.entity.Measure;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface MeasureRepository extends JpaRepository<Measure, UUID> {

    List<Measure> findAllByAssessmentIdOrderByImplementedAtAsc(UUID assessmentId);

    Page<Measure> findAllByAshaWorkerId(UUID ashaWorkerId, Pageable pageable);
}
