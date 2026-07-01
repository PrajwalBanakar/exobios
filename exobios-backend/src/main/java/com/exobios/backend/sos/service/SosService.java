package com.exobios.backend.sos.service;

import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.common.exception.BadRequestException;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.sos.dto.CreateSosRequest;
import com.exobios.backend.sos.dto.SosRecordDto;
import com.exobios.backend.sos.entity.SosRecord;
import com.exobios.backend.sos.entity.enums.SosStatus;
import com.exobios.backend.sos.exception.SosRecordNotFoundException;
import com.exobios.backend.sos.mapper.SosMapper;
import com.exobios.backend.sos.repository.SosRepository;
import com.exobios.backend.users.entity.enums.Role;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.UUID;

@Slf4j
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class SosService {

    private final SosRepository sosRepository;
    private final SosMapper     sosMapper;

    @Transactional
    public SosRecordDto createSos(CreateSosRequest request, UserPrincipal principal) {
        SosRecord sos = new SosRecord();
        sos.setPatientId(request.getPatientId());
        sos.setAssessmentId(request.getAssessmentId());
        sos.setAshaWorkerId(principal.getId());
        sos.setType(request.getType());
        sos.setDescription(request.getDescription());
        sos.setLatitude(request.getLatitude());
        sos.setLongitude(request.getLongitude());
        sos.setStatus(SosStatus.ACTIVE);

        SosRecord saved = sosRepository.save(sos);
        log.warn("SOS CREATED id={} type={} ashaWorker={} patient={}",
                saved.getId(), saved.getType(), principal.getId(), request.getPatientId());
        return sosMapper.toDto(saved);
    }

    public SosRecordDto getSosById(UUID id, UserPrincipal principal) {
        SosRecord sos = findOrThrow(id);
        assertOwnership(sos, principal);
        return sosMapper.toDto(sos);
    }

    public PageResponse<SosRecordDto> listSosRecords(SosStatus status, Pageable pageable,
                                                      UserPrincipal principal) {
        Page<SosRecord> page;
        if (isAsha(principal)) {
            page = status != null
                    ? sosRepository.findAllByAshaWorkerIdAndStatus(principal.getId(), status, pageable)
                    : sosRepository.findAllByAshaWorkerId(principal.getId(), pageable);
        } else {
            page = status != null
                    ? sosRepository.findAllByStatus(status, pageable)
                    : sosRepository.findAll(pageable);
        }
        return PageResponse.of(page.map(sosMapper::toDto));
    }

    @Transactional
    public SosRecordDto updateSosStatus(UUID id, SosStatus newStatus, UserPrincipal principal) {
        SosRecord sos = findOrThrow(id);

        if (isAsha(principal)) {
            assertOwnership(sos, principal);
            if (newStatus != SosStatus.CANCELLED) {
                throw new ForbiddenException("ASHA workers can only cancel their own SOS records");
            }
            if (sos.getStatus() != SosStatus.ACTIVE) {
                throw new BadRequestException("Only ACTIVE SOS records can be cancelled");
            }
        }

        sos.setStatus(newStatus);
        if (newStatus == SosStatus.RESOLVED) {
            sos.setResolvedAt(Instant.now());
        }
        log.info("SOS id={} status updated to {}", id, newStatus);
        return sosMapper.toDto(sosRepository.save(sos));
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private SosRecord findOrThrow(UUID id) {
        return sosRepository.findById(id).orElseThrow(() -> new SosRecordNotFoundException(id));
    }

    private void assertOwnership(SosRecord sos, UserPrincipal principal) {
        if (isAsha(principal) && !sos.getAshaWorkerId().equals(principal.getId())) {
            throw new ForbiddenException("Access denied: this SOS record belongs to a different ASHA worker");
        }
    }

    private boolean isAsha(UserPrincipal principal) {
        return Role.ASHA.name().equals(principal.getRole());
    }
}
