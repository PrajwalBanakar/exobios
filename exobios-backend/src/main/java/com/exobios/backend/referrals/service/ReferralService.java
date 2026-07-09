package com.exobios.backend.referrals.service;

import com.exobios.backend.assessments.entity.Assessment;
import com.exobios.backend.assessments.entity.enums.AssessmentStatus;
import com.exobios.backend.assessments.exception.AssessmentNotFoundException;
import com.exobios.backend.assessments.repository.AssessmentRepository;
import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.common.exception.BadRequestException;
import com.exobios.backend.common.exception.ConflictException;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.common.exception.ResourceNotFoundException;
import com.exobios.backend.patients.repository.PatientRepository;
import com.exobios.backend.referrals.dto.CreateReferralRequest;
import com.exobios.backend.referrals.dto.ReferralClinicalNoteDto;
import com.exobios.backend.referrals.dto.ReferralDto;
import com.exobios.backend.referrals.dto.UpdateReferralRequest;
import com.exobios.backend.referrals.entity.Referral;
import com.exobios.backend.referrals.entity.ReferralClinicalNote;
import com.exobios.backend.referrals.entity.enums.ReferralReviewStage;
import com.exobios.backend.referrals.entity.enums.ReferralStatus;
import com.exobios.backend.referrals.exception.ReferralNotFoundException;
import com.exobios.backend.referrals.mapper.ReferralClinicalNoteMapper;
import com.exobios.backend.referrals.mapper.ReferralMapper;
import com.exobios.backend.referrals.repository.ReferralClinicalNoteRepository;
import com.exobios.backend.referrals.repository.ReferralRepository;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.users.entity.User;
import com.exobios.backend.users.entity.enums.Role;
import com.exobios.backend.users.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.exobios.backend.audit.annotation.Auditable;
import com.exobios.backend.audit.entity.enums.AuditAction;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

@Slf4j
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class ReferralService {

    private static final Map<ReferralReviewStage, Set<ReferralReviewStage>> ALLOWED_REVIEW_STAGE_TRANSITIONS = Map.of(
            ReferralReviewStage.ASSIGNED_TO_DOCTOR, Set.of(ReferralReviewStage.UNDER_REVIEW),
            ReferralReviewStage.UNDER_REVIEW,       Set.of(ReferralReviewStage.ACTION_TAKEN),
            ReferralReviewStage.ACTION_TAKEN,       Set.of(ReferralReviewStage.CLOSED)
    );

    private final ReferralRepository             referralRepository;
    private final AssessmentRepository           assessmentRepository;
    private final PatientRepository              patientRepository;
    private final UserRepository                 userRepository;
    private final ReferralMapper                 referralMapper;
    private final ReferralClinicalNoteRepository referralClinicalNoteRepository;
    private final ReferralClinicalNoteMapper     referralClinicalNoteMapper;

    // ── Create ────────────────────────────────────────────────────────────────

    @Auditable(action = AuditAction.REFER, entityType = "REFERRAL")
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

    public PageResponse<ReferralDto> getReferrals(UUID patientId, ReferralStatus status, Boolean unassigned,
                                                   Pageable pageable, UserPrincipal principal) {
        Page<Referral> page;
        if (patientId != null) {
            // Scope to the caller's own patients when ASHA — matches every other
            // ownership-checked list method in this codebase (see assertReferralOwnership).
            page = isAsha(principal)
                    ? referralRepository.findAllByPatientIdAndAshaWorkerId(patientId, principal.getId(), pageable)
                    : referralRepository.findAllByPatientId(patientId, pageable);
        } else if (Boolean.TRUE.equals(unassigned) && isDoctor(principal)) {
            // The claimable inbox — by definition nobody is assigned yet, so this is
            // unscoped even though the caller is a DOCTOR.
            page = referralRepository.findAllByReviewStageAndAssignedDoctorIdIsNull(
                    ReferralReviewStage.CREATED, pageable);
        } else if (isDoctor(principal)) {
            page = referralRepository.findAllByAssignedDoctorId(principal.getId(), pageable);
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
        if (!patientRepository.existsById(patientId)) {
            throw new ResourceNotFoundException("Patient", patientId);
        }
        Page<Referral> page = isAsha(principal)
                ? referralRepository.findAllByPatientIdAndAshaWorkerId(patientId, principal.getId(), pageable)
                : referralRepository.findAllByPatientId(patientId, pageable);
        return PageResponse.of(page.map(referralMapper::toDto));
    }

    // ── Update ────────────────────────────────────────────────────────────────

    @Auditable(action = AuditAction.UPDATE, entityType = "REFERRAL")
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

    @Auditable(action = AuditAction.STATUS_CHANGE, entityType = "REFERRAL")
    @Transactional
    public ReferralDto updateStatus(UUID id, ReferralStatus newStatus, UserPrincipal principal) {
        Referral referral = findOrThrow(id);
        assertReferralOwnership(referral, principal);

        referral.setStatus(newStatus);
        log.info("Referral id={} status changed to {}", id, newStatus);
        return referralMapper.toDto(referralRepository.save(referral));
    }

    // ── Doctor review ────────────────────────────────────────────────────────

    @Auditable(action = AuditAction.ASSIGN, entityType = "REFERRAL")
    @Transactional
    public ReferralDto claimReferral(UUID id, UserPrincipal principal) {
        Referral referral = findOrThrow(id);
        if (referral.getAssignedDoctorId() != null) {
            throw new ConflictException("Referral is already assigned to a doctor");
        }
        referral.setAssignedDoctorId(principal.getId());
        referral.setReviewStage(ReferralReviewStage.ASSIGNED_TO_DOCTOR);
        log.info("Referral id={} claimed by doctor={}", id, principal.getId());
        return referralMapper.toDto(referralRepository.save(referral));
    }

    @Auditable(action = AuditAction.ASSIGN, entityType = "REFERRAL")
    @Transactional
    public ReferralDto assignDoctor(UUID id, UUID doctorId, UserPrincipal principal) {
        Referral referral = findOrThrow(id);
        User doctor = userRepository.findById(doctorId)
                .orElseThrow(() -> new BadRequestException("No such doctor: " + doctorId));
        if (doctor.getRole() != Role.DOCTOR) {
            throw new BadRequestException("User " + doctorId + " is not a DOCTOR");
        }
        referral.setAssignedDoctorId(doctorId);
        if (referral.getReviewStage() == ReferralReviewStage.CREATED) {
            referral.setReviewStage(ReferralReviewStage.ASSIGNED_TO_DOCTOR);
        }
        log.info("Referral id={} assigned to doctor={} by admin={}", id, doctorId, principal.getId());
        return referralMapper.toDto(referralRepository.save(referral));
    }

    @Auditable(action = AuditAction.STATUS_CHANGE, entityType = "REFERRAL")
    @Transactional
    public ReferralDto updateReviewStage(UUID id, ReferralReviewStage newStage, UserPrincipal principal) {
        Referral referral = findOrThrow(id);
        assertDoctorAssignment(referral, principal);

        ReferralReviewStage currentStage = referral.getReviewStage();
        Set<ReferralReviewStage> allowed = ALLOWED_REVIEW_STAGE_TRANSITIONS.getOrDefault(currentStage, Set.of());
        if (!allowed.contains(newStage)) {
            throw new BadRequestException(
                    "Invalid review stage transition: " + currentStage + " → " + newStage);
        }

        referral.setReviewStage(newStage);
        log.info("Referral id={} review stage changed to {}", id, newStage);
        return referralMapper.toDto(referralRepository.save(referral));
    }

    @Auditable(action = AuditAction.REVIEW, entityType = "REFERRAL")
    @Transactional
    public ReferralClinicalNoteDto addClinicalNote(UUID referralId, String note, UserPrincipal principal) {
        findOrThrow(referralId);
        ReferralClinicalNote clinicalNote = new ReferralClinicalNote();
        clinicalNote.setReferralId(referralId);
        clinicalNote.setNote(note);
        ReferralClinicalNote saved = referralClinicalNoteRepository.save(clinicalNote);
        log.info("Clinical note added to referral id={} by={}", referralId, principal.getId());
        return referralClinicalNoteMapper.toDto(saved);
    }

    public List<ReferralClinicalNoteDto> getClinicalNotes(UUID referralId, UserPrincipal principal) {
        findOrThrow(referralId);
        return referralClinicalNoteMapper.toDtoList(
                referralClinicalNoteRepository.findAllByReferralIdOrderByCreatedAtDesc(referralId));
    }

    @Auditable(action = AuditAction.RECOMMEND, entityType = "REFERRAL")
    @Transactional
    public ReferralDto setRecommendation(UUID id, String recommendation, UserPrincipal principal) {
        Referral referral = findOrThrow(id);
        referral.setDoctorRecommendation(recommendation);
        log.info("Recommendation set on referral id={} by={}", id, principal.getId());
        return referralMapper.toDto(referralRepository.save(referral));
    }

    // ── Delete ────────────────────────────────────────────────────────────────

    @Auditable(action = AuditAction.DELETE, entityType = "REFERRAL", entityIdArgIndex = 0)
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

    private boolean isDoctor(UserPrincipal principal) {
        return Role.DOCTOR.name().equals(principal.getRole());
    }

    private void assertDoctorAssignment(Referral referral, UserPrincipal principal) {
        if (isDoctor(principal)
                && (referral.getAssignedDoctorId() == null
                    || !referral.getAssignedDoctorId().equals(principal.getId()))) {
            throw new ForbiddenException("Access denied: this referral is not assigned to you");
        }
    }
}
