package com.exobios.backend.measures.service;

import com.exobios.backend.assessments.entity.Assessment;
import com.exobios.backend.assessments.entity.enums.AssessmentStatus;
import com.exobios.backend.assessments.exception.AssessmentNotFoundException;
import com.exobios.backend.assessments.repository.AssessmentRepository;
import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.measures.dto.CreateMeasureRequest;
import com.exobios.backend.measures.dto.MeasureDto;
import com.exobios.backend.measures.dto.UpdateMeasureRequest;
import com.exobios.backend.measures.entity.Measure;
import com.exobios.backend.measures.exception.MeasureNotFoundException;
import com.exobios.backend.measures.mapper.MeasureMapper;
import com.exobios.backend.measures.repository.MeasureRepository;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.users.entity.enums.Role;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class MeasureService {

    private final MeasureRepository    measureRepository;
    private final AssessmentRepository assessmentRepository;
    private final MeasureMapper        measureMapper;

    // ── Create ────────────────────────────────────────────────────────────────

    @Transactional
    public MeasureDto createMeasure(CreateMeasureRequest request, UserPrincipal principal) {
        Assessment assessment = assessmentRepository.findById(request.getAssessmentId())
                .orElseThrow(() -> new AssessmentNotFoundException(request.getAssessmentId()));

        assertAssessmentNotDraft(assessment);
        assertAssessmentOwnership(assessment, principal);

        Measure measure = new Measure();
        measure.setAssessmentId(assessment.getId());
        measure.setPatientId(assessment.getPatientId());
        measure.setAshaWorkerId(assessment.getAshaWorkerId());
        measure.setAction(request.getAction());
        measure.setCategory(request.getCategory());
        measure.setDescription(request.getDescription());
        measure.setImplementedAt(request.getImplementedAt() != null
                ? request.getImplementedAt() : Instant.now());
        measure.setImplementedBy(request.getImplementedBy() != null
                ? request.getImplementedBy() : principal.getPhone());
        measure.setOutcome(request.getOutcome());
        measure.setNotes(request.getNotes());

        Measure saved = measureRepository.save(measure);
        log.info("Created measure id={} for assessment={}", saved.getId(), assessment.getId());
        return measureMapper.toDto(saved);
    }

    // ── Read ──────────────────────────────────────────────────────────────────

    public MeasureDto getMeasureById(UUID id, UserPrincipal principal) {
        Measure measure = findOrThrow(id);
        assertMeasureOwnership(measure, principal);
        return measureMapper.toDto(measure);
    }

    public List<MeasureDto> getAssessmentTimeline(UUID assessmentId, UserPrincipal principal) {
        Assessment assessment = assessmentRepository.findById(assessmentId)
                .orElseThrow(() -> new AssessmentNotFoundException(assessmentId));
        assertAssessmentOwnership(assessment, principal);
        return measureMapper.toDtoList(
                measureRepository.findAllByAssessmentIdOrderByImplementedAtAsc(assessmentId));
    }

    public PageResponse<MeasureDto> getAllMeasures(Pageable pageable, UserPrincipal principal) {
        if (isAsha(principal)) {
            return PageResponse.of(
                    measureRepository.findAllByAshaWorkerId(principal.getId(), pageable)
                            .map(measureMapper::toDto));
        }
        return PageResponse.of(measureRepository.findAll(pageable).map(measureMapper::toDto));
    }

    // ── Update ────────────────────────────────────────────────────────────────

    @Transactional
    public MeasureDto updateMeasure(UUID id, UpdateMeasureRequest request, UserPrincipal principal) {
        Measure measure = findOrThrow(id);
        assertMeasureOwnership(measure, principal);

        measure.setAction(request.getAction());
        measure.setCategory(request.getCategory());
        measure.setDescription(request.getDescription());
        if (request.getImplementedAt() != null) measure.setImplementedAt(request.getImplementedAt());
        if (request.getImplementedBy() != null) measure.setImplementedBy(request.getImplementedBy());
        measure.setOutcome(request.getOutcome());
        measure.setNotes(request.getNotes());

        return measureMapper.toDto(measureRepository.save(measure));
    }

    // ── Delete ────────────────────────────────────────────────────────────────

    @Transactional
    public void deleteMeasure(UUID id, UserPrincipal principal) {
        Measure measure = findOrThrow(id);
        assertMeasureOwnership(measure, principal);
        measureRepository.delete(measure);
        log.info("Deleted measure id={}", id);
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private Measure findOrThrow(UUID id) {
        return measureRepository.findById(id).orElseThrow(() -> new MeasureNotFoundException(id));
    }

    private void assertAssessmentNotDraft(Assessment assessment) {
        if (assessment.getStatus() == AssessmentStatus.DRAFT) {
            throw new com.exobios.backend.common.exception.BadRequestException(
                    "Cannot add measures to a DRAFT assessment — submit it first");
        }
    }

    private void assertAssessmentOwnership(Assessment assessment, UserPrincipal principal) {
        if (isAsha(principal) && !assessment.getAshaWorkerId().equals(principal.getId())) {
            throw new ForbiddenException("Access denied: this assessment belongs to a different ASHA worker");
        }
    }

    private void assertMeasureOwnership(Measure measure, UserPrincipal principal) {
        if (isAsha(principal) && !measure.getAshaWorkerId().equals(principal.getId())) {
            throw new ForbiddenException("Access denied: this measure belongs to a different ASHA worker");
        }
    }

    private boolean isAsha(UserPrincipal principal) {
        return Role.ASHA.name().equals(principal.getRole());
    }
}
