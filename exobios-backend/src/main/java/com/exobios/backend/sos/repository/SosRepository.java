package com.exobios.backend.sos.repository;

import com.exobios.backend.sos.entity.SosRecord;
import com.exobios.backend.sos.entity.enums.SosStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface SosRepository extends JpaRepository<SosRecord, UUID> {

    Page<SosRecord> findAllByAshaWorkerId(UUID ashaWorkerId, Pageable pageable);

    Page<SosRecord> findAllByAshaWorkerIdAndStatus(UUID ashaWorkerId, SosStatus status, Pageable pageable);

    Page<SosRecord> findAllByStatus(SosStatus status, Pageable pageable);
}
