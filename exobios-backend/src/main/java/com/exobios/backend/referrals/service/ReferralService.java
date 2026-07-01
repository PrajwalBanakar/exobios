package com.exobios.backend.referrals.service;

import com.exobios.backend.assessments.entity.Assessment;
import com.exobios.backend.assessments.entity.enums.AssessmentStatus;
import com.exobios.backend.assessments.exception.AssessmentNotFoundException;
import com.exobios.backend.assessments.repository.AssessmentRepository;
import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.common.exception.BadRequestException;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.referrals.dto.CreateReferralRequest;
import com.exobios.backend.referrals.dto.ReferralDto;
import com.exobios.backend.referrals.dto.UpdateReferralRequest;
import com.exobios.backend.referrals.entity.Referral;
import com.exobios.backend.referrals.entity.enums.ReferralStatus;
import com.exobios.backend.referrals.exception.ReferralNotFoundException;
import com.exobios.backend.referrals.mapper.ReferralMapper;
import com.exobios.backend.referrals.repository.ReferralRepository;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.users.entity.enums.Role;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class ReferralService {

    private final ReferralRepository   referralRepository;
    private final AssessmentRepository assessmentRepository;
    private final ReferralMapper       referralMapper;

    // ── Create ────────────────────────────────────────────────────────────────

    @Transactional
    public ReferralDto createReferral(CreateReferralRequest request, UserPrincipal principal) {
        Assessment assessment = assessmentRepository.findById(request.getAssessmentId())
                .orElseThrow(() -> new AssessmentNotFoundException(request.getAssessmentId()));

        assertAssessmentSubmitted(assessment);
        assertAssessmentOwnership(assessment, principal);

        Referral referral = new Referral();
        referral.setAssessmentId(assessment.getId());
        referral.setPatientId(assessment.getPatientId());
        referral.setAshaWorkerId(assessment.getAshaWorkerId());
        referral.setReferralHospital(request.getReferralHospital());
        referral.setReferralDoctor(request.getReferralDoctor());
        referral.setReferralReason(request.getReferralReason());
        referral.setPriority(request.getPriority() != null
                ? request.getPriority() : com.exobios.backend.referrals.entity.enums.ReferralPriority.MEDIUM);
        referral.setStatus(ReferralStatus.PENDING);
        referral.setFollowUpDate(request.getFollowUpDate());

        Referral saved = referralRepository.save(referral);
        log.info("Created referral id={} for assessment={}", saved.getId(), assessment.getId());
        return referralMapper.toDto(saved);
    }

    // ── Read ──────────────────────────────────────────────────────────────────

    public ReferralDto getReferralById(UUID id, UserPrincipal principal) {
        Referral referral = findOrThrow(id);
        assertReferralOwnership(referral, principal);
        return referralMapper.toDto(referral);
    }

    public PageResponse<ReferralDto> getReferrals(UUID patientId, ReferralStatus status,
                                                   Pageable pageable, UserPrincipal principal) {
        Page<Referral> page;
        if (patientId != null) {
            page = referralRepository.findAllByPatientId(patientId, pageable);
        } else if (isAsha(principal)) {
            page = status != null
                    ? referralRepository.findAllByAshaWorkerIdAndStatus(principal.getId(), status, pageable)
                    : referralRepository.findAllByAshaWorkerId(principal.getId(), pageable);
        } else {
            page = status != null
                    ? referralRepository.findAllByStatus(status, pageable)
                    : referralRepository.findAll(pageable);
        }
        return PageResponse.of(page.map(referralMapper::toDto));
    }

    public List<ReferralDto> getAssessmentReferrals(UUID assessmentId, UserPrincipal principal) {
        Assessment assessment = assessmentRepository.findById(assessmentId)
                .orElseThrow(() -> new AssessmentNotFoundException(assessmentId));
        assertAssessmentOwnership(assessment, principal);
        return referralMapper.toDtoList(
                referralRepository.findAllByAssessmentIdOrderByCreatedAtDesc(assessmentId));
    }

    public PageResponse<ReferralDto> getPatientReferrals(UUID patientId, Pageable pageable,
                                                          UserPrincipal principal) {
        return PageResponse.of(referralRepository.findAllByPatientId(patientId, pageable)
                .map(referralMapper::toDto));
    }

    // ── Update ────────────────────────────────────────────────────────────────

    @Transactional
    public ReferralDto updateReferral(UUID id, UpdateReferralRequest request,
                                      UserPrincipal principal) {
        Referral referral = findOrThrow(id);
        assertReferralOwnership(referral, principal);
        assertReferralMutable(referral);

        if (StringUtils.hasText(request.getReferralHospital()))
            referral.setReferralHospital(request.getReferralHospital());
        if (StringUtils.hasText(request.getReferralDoctor()))
            referral.setReferralDoctor(request.getReferralDoctor());
        if (StringUtils.hasText(request.getReferralReason()))
            referral.setReferralReason(request.getReferralReason());
        if (request.getPriority() != null) referral.setPriority(request.getPriority());
        if (request.getFollowUpDate() != null) referral.setFollowUpDate(request.getFollowUpDate());

        return referralMapper.toDto(referralRepository.save(referral));
    }

    @Transactional
    public ReferralDto updateStatus(UUID id, ReferralStatus newStatus, UserPrincipal principal) {
        Referral referral = findOrThrow(id);
        assertReferralOwnership(referral, principal);

        referral.setStatus(newStatus);
        log.info("Referral id={} status changed to {}", id, newStatus);
        return referralMapper.toDto(referralRepository.save(referral));
    }

    // ── Delete ────────────────────────────────────────────────────────────────

    @Transactional
    public void deleteReferral(UUID id, UserPrincipal principal) {
        Referral referral = findOrThrow(id);
        assertReferralOwnership(referral, principal);
        assertReferralMutable(referral);
        referralRepository.delete(referral);
        log.info("Deleted referral id={}", id);
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private Referral findOrThrow(UUID id) {
        return referralRepository.findById(id)
                .orElseThrow(() -> new ReferralNotFoundException(id));
    }

    private void assertAssessmentSubmitted(Assessment assessment) {
        if (assessment.getStatus() == AssessmentStatus.DRAFT) {
            throw new BadRequestException(
                    "Cannot create a referral for a DRAFT assessment — submit the assessment first");
        }
    }

    private void assertAssessmentOwnership(Assessment assessment, UserPrincipal principal) {
        if (isAsha(principal) && !assessment.getAshaWorkerId().equals(principal.getId())) {
            throw new ForbiddenException("Access denied: this assessment belongs to a different ASHA worker");
        }
    }

    private void assertReferralOwnership(Referral referral, UserPrincipal principal) {
        if (isAsha(principal) && !referral.getAshaWorkerId().equals(principal.getId())) {
            throw new ForbiddenException("Access denied: this referral belongs to a different ASHA worker");
        }
    }

    private void assertReferralMutable(Referral referral) {
        if (referral.getStatus() == ReferralStatus.COMPLETED
                || referral.getStatus() == ReferralStatus.CANCELLED) {
            throw new BadRequestException(
                    "Referral cannot be modified — status is " + referral.getStatus());
        }
    }

    private boolean isAsha(UserPrincipal principal) {
        return Role.ASHA.name().equals(principal.getRole());
    }
}
