package com.exobios.backend.referrals.service;

import com.exobios.backend.assessments.entity.Assessment;
import com.exobios.backend.assessments.entity.enums.AssessmentStatus;
import com.exobios.backend.assessments.exception.AssessmentNotFoundException;
import com.exobios.backend.assessments.repository.AssessmentRepository;
import com.exobios.backend.common.exception.BadRequestException;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.common.exception.ResourceNotFoundException;
import com.exobios.backend.patients.repository.PatientRepository;
import com.exobios.backend.common.exception.ConflictException;
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
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ReferralServiceTest {

    @Mock private ReferralRepository             referralRepository;
    @Mock private AssessmentRepository           assessmentRepository;
    @Mock private PatientRepository              patientRepository;
    @Mock private UserRepository                 userRepository;
    @Mock private ReferralMapper                 referralMapper;
    @Mock private ReferralClinicalNoteRepository referralClinicalNoteRepository;
    @Mock private ReferralClinicalNoteMapper     referralClinicalNoteMapper;

    private ReferralService referralService;

    private final UUID ashaId    = UUID.randomUUID();
    private final UUID otherAsha = UUID.randomUUID();
    private final UUID doctorId  = UUID.randomUUID();

    @BeforeEach
    void setUp() {
        referralService = new ReferralService(referralRepository, assessmentRepository, patientRepository,
                userRepository, referralMapper, referralClinicalNoteRepository, referralClinicalNoteMapper);
        lenient().when(referralMapper.toDto(any(Referral.class))).thenAnswer(inv -> {
            Referral r = inv.getArgument(0);
            return ReferralDto.builder().id(r.getId()).ashaWorkerId(r.getAshaWorkerId()).status(r.getStatus()).build();
        });
        lenient().when(referralMapper.toDtoList(org.mockito.ArgumentMatchers.anyList())).thenAnswer(inv -> {
            List<Referral> list = inv.getArgument(0);
            return list.stream().map(r -> ReferralDto.builder().id(r.getId()).ashaWorkerId(r.getAshaWorkerId()).build()).toList();
        });
    }

    private UserPrincipal asha(UUID id)   { return UserPrincipal.fromToken(id.toString(), "9876543210", "ASHA"); }
    private UserPrincipal admin(UUID id)  { return UserPrincipal.fromToken(id.toString(), "9000000000", "SUPER_ADMIN"); }
    private UserPrincipal doctor(UUID id) { return UserPrincipal.fromToken(id.toString(), "9876500002", "DOCTOR"); }

    private Assessment assessment(UUID owner, AssessmentStatus status) {
        Assessment a = new Assessment();
        ReflectionTestUtils.setField(a, "id", UUID.randomUUID());
        a.setPatientId(UUID.randomUUID());
        a.setAshaWorkerId(owner);
        a.setStatus(status);
        return a;
    }

    private Referral existingReferral(UUID id, UUID owner, ReferralStatus status) {
        Referral r = new Referral();
        ReflectionTestUtils.setField(r, "id", id);
        r.setAssessmentId(UUID.randomUUID());
        r.setPatientId(UUID.randomUUID());
        r.setAshaWorkerId(owner);
        r.setReferralReason("Needs specialist evaluation");
        r.setStatus(status);
        return r;
    }

    // ── createReferral — assessment must be SUBMITTED (not DRAFT) + owned ───────

    @Test
    void createReferral_forDraftAssessment_throwsBadRequest() {
        Assessment draft = assessment(ashaId, AssessmentStatus.DRAFT);
        CreateReferralRequest req = new CreateReferralRequest();
        req.setAssessmentId(draft.getId());
        req.setReferralReason("Needs specialist evaluation");
        when(assessmentRepository.findById(draft.getId())).thenReturn(Optional.of(draft));

        assertThatThrownBy(() -> referralService.createReferral(req, asha(ashaId)))
                .isInstanceOf(BadRequestException.class);
        verify(referralRepository, never()).save(any());
    }

    @Test
    void createReferral_forAnotherAshasAssessment_throwsForbidden() {
        Assessment a = assessment(otherAsha, AssessmentStatus.SUBMITTED);
        CreateReferralRequest req = new CreateReferralRequest();
        req.setAssessmentId(a.getId());
        req.setReferralReason("Needs specialist evaluation");
        when(assessmentRepository.findById(a.getId())).thenReturn(Optional.of(a));

        assertThatThrownBy(() -> referralService.createReferral(req, asha(ashaId)))
                .isInstanceOf(ForbiddenException.class);
    }

    @Test
    void createReferral_defaultsStatusToPendingAndInheritsAssessmentOwnership() {
        Assessment a = assessment(ashaId, AssessmentStatus.SUBMITTED);
        CreateReferralRequest req = new CreateReferralRequest();
        req.setAssessmentId(a.getId());
        req.setReferralReason("Needs specialist evaluation");
        when(assessmentRepository.findById(a.getId())).thenReturn(Optional.of(a));
        when(referralRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        ReferralDto result = referralService.createReferral(req, asha(ashaId));

        assertThat(result.getStatus()).isEqualTo(ReferralStatus.PENDING);
        assertThat(result.getAshaWorkerId()).isEqualTo(ashaId);
    }

    // ── getReferrals — IDOR regression guard (ownership scoping by patientId) ───

    @Test
    void getReferrals_withPatientIdFilter_asAsha_isScopedToOwnPatients() {
        UUID patientId = UUID.randomUUID();
        Pageable pageable = PageRequest.of(0, 20);
        when(referralRepository.findAllByPatientIdAndAshaWorkerId(patientId, ashaId, pageable))
                .thenReturn(new PageImpl<>(List.of()));

        referralService.getReferrals(patientId, null, null, pageable, asha(ashaId));

        verify(referralRepository).findAllByPatientIdAndAshaWorkerId(patientId, ashaId, pageable);
        // The unscoped variant must never be reached for an ASHA caller — this is the
        // exact IDOR that let one ASHA worker read another's patient referrals.
        verify(referralRepository, never()).findAllByPatientId(any(), any());
    }

    @Test
    void getReferrals_withPatientIdFilter_asSuperAdmin_isUnscoped() {
        UUID patientId = UUID.randomUUID();
        Pageable pageable = PageRequest.of(0, 20);
        when(referralRepository.findAllByPatientId(patientId, pageable)).thenReturn(new PageImpl<>(List.of()));

        referralService.getReferrals(patientId, null, null, pageable, admin(UUID.randomUUID()));

        verify(referralRepository).findAllByPatientId(patientId, pageable);
    }

    @Test
    void getReferrals_withoutPatientIdFilter_asAsha_scopedByAshaWorkerId() {
        Pageable pageable = PageRequest.of(0, 20);
        when(referralRepository.findAllByAshaWorkerId(ashaId, pageable)).thenReturn(new PageImpl<>(List.of()));

        referralService.getReferrals(null, null, null, pageable, asha(ashaId));

        verify(referralRepository).findAllByAshaWorkerId(ashaId, pageable);
    }

    @Test
    void getReferrals_asDoctor_withoutUnassignedFlag_isScopedToAssignedDoctor() {
        Pageable pageable = PageRequest.of(0, 20);
        when(referralRepository.findAllByAssignedDoctorId(doctorId, pageable)).thenReturn(new PageImpl<>(List.of()));

        referralService.getReferrals(null, null, null, pageable, doctor(doctorId));

        verify(referralRepository).findAllByAssignedDoctorId(doctorId, pageable);
    }

    @Test
    void getReferrals_asDoctor_withUnassignedFlag_returnsSharedInbox() {
        Pageable pageable = PageRequest.of(0, 20);
        when(referralRepository.findAllByReviewStageAndAssignedDoctorIdIsNull(ReferralReviewStage.CREATED, pageable))
                .thenReturn(new PageImpl<>(List.of()));

        referralService.getReferrals(null, null, true, pageable, doctor(doctorId));

        verify(referralRepository).findAllByReviewStageAndAssignedDoctorIdIsNull(ReferralReviewStage.CREATED, pageable);
        verify(referralRepository, never()).findAllByAssignedDoctorId(any(), any());
    }

    // ── getPatientReferrals — existence check + ownership scoping ───────────────

    @Test
    void getPatientReferrals_forUnknownPatient_throwsResourceNotFound() {
        UUID patientId = UUID.randomUUID();
        when(patientRepository.existsById(patientId)).thenReturn(false);

        assertThatThrownBy(() -> referralService.getPatientReferrals(patientId, PageRequest.of(0, 20), asha(ashaId)))
                .isInstanceOf(ResourceNotFoundException.class);
    }

    @Test
    void getPatientReferrals_asAsha_isScopedToOwnPatients() {
        UUID patientId = UUID.randomUUID();
        Pageable pageable = PageRequest.of(0, 20);
        when(patientRepository.existsById(patientId)).thenReturn(true);
        when(referralRepository.findAllByPatientIdAndAshaWorkerId(patientId, ashaId, pageable))
                .thenReturn(new PageImpl<>(List.of()));

        referralService.getPatientReferrals(patientId, pageable, asha(ashaId));

        verify(referralRepository).findAllByPatientIdAndAshaWorkerId(patientId, ashaId, pageable);
        verify(referralRepository, never()).findAllByPatientId(any(), any());
    }

    // ── updateReferral / deleteReferral — immutable once COMPLETED/CANCELLED ────

    @Test
    void updateReferral_onCompletedReferral_throwsBadRequest() {
        UUID id = UUID.randomUUID();
        when(referralRepository.findById(id)).thenReturn(Optional.of(existingReferral(id, ashaId, ReferralStatus.COMPLETED)));
        UpdateReferralRequest req = new UpdateReferralRequest();
        req.setReferralHospital("City Hospital");

        assertThatThrownBy(() -> referralService.updateReferral(id, req, asha(ashaId)))
                .isInstanceOf(BadRequestException.class);
    }

    @Test
    void updateReferral_onCancelledReferral_throwsBadRequest() {
        UUID id = UUID.randomUUID();
        when(referralRepository.findById(id)).thenReturn(Optional.of(existingReferral(id, ashaId, ReferralStatus.CANCELLED)));
        UpdateReferralRequest req = new UpdateReferralRequest();
        req.setReferralHospital("City Hospital");

        assertThatThrownBy(() -> referralService.updateReferral(id, req, asha(ashaId)))
                .isInstanceOf(BadRequestException.class);
    }

    @Test
    void updateReferral_onPendingReferral_succeeds() {
        UUID id = UUID.randomUUID();
        Referral referral = existingReferral(id, ashaId, ReferralStatus.PENDING);
        when(referralRepository.findById(id)).thenReturn(Optional.of(referral));
        when(referralRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));
        UpdateReferralRequest req = new UpdateReferralRequest();
        req.setReferralHospital("City Hospital");

        referralService.updateReferral(id, req, asha(ashaId));

        assertThat(referral.getReferralHospital()).isEqualTo("City Hospital");
    }

    @Test
    void updateReferral_asNonOwningAsha_throwsForbidden() {
        UUID id = UUID.randomUUID();
        when(referralRepository.findById(id)).thenReturn(Optional.of(existingReferral(id, otherAsha, ReferralStatus.PENDING)));
        UpdateReferralRequest req = new UpdateReferralRequest();

        assertThatThrownBy(() -> referralService.updateReferral(id, req, asha(ashaId)))
                .isInstanceOf(ForbiddenException.class);
    }

    @Test
    void deleteReferral_onAcceptedReferral_succeeds() {
        UUID id = UUID.randomUUID();
        Referral referral = existingReferral(id, ashaId, ReferralStatus.ACCEPTED);
        when(referralRepository.findById(id)).thenReturn(Optional.of(referral));

        referralService.deleteReferral(id, asha(ashaId));

        verify(referralRepository).delete(referral);
    }

    @Test
    void deleteReferral_onCompletedReferral_throwsBadRequestAndDoesNotDelete() {
        UUID id = UUID.randomUUID();
        when(referralRepository.findById(id)).thenReturn(Optional.of(existingReferral(id, ashaId, ReferralStatus.COMPLETED)));

        assertThatThrownBy(() -> referralService.deleteReferral(id, asha(ashaId)))
                .isInstanceOf(BadRequestException.class);
        verify(referralRepository, never()).delete(any());
    }

    @Test
    void getReferralById_unknownId_throwsReferralNotFound() {
        UUID id = UUID.randomUUID();
        when(referralRepository.findById(id)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> referralService.getReferralById(id, asha(ashaId)))
                .isInstanceOf(ReferralNotFoundException.class);
    }

    @Test
    void getAssessmentReferrals_forUnknownAssessment_throwsAssessmentNotFound() {
        UUID assessmentId = UUID.randomUUID();
        when(assessmentRepository.findById(assessmentId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> referralService.getAssessmentReferrals(assessmentId, asha(ashaId)))
                .isInstanceOf(AssessmentNotFoundException.class);
    }

    // ── claimReferral ────────────────────────────────────────────────────────

    @Test
    void claimReferral_whenUnassigned_setsAssigneeAndAdvancesStage() {
        UUID id = UUID.randomUUID();
        Referral referral = existingReferral(id, ashaId, ReferralStatus.PENDING);
        when(referralRepository.findById(id)).thenReturn(Optional.of(referral));
        when(referralRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        referralService.claimReferral(id, doctor(doctorId));

        assertThat(referral.getAssignedDoctorId()).isEqualTo(doctorId);
        assertThat(referral.getReviewStage()).isEqualTo(ReferralReviewStage.ASSIGNED_TO_DOCTOR);
    }

    @Test
    void claimReferral_whenAlreadyAssigned_throwsConflict() {
        UUID id = UUID.randomUUID();
        Referral referral = existingReferral(id, ashaId, ReferralStatus.PENDING);
        referral.setAssignedDoctorId(UUID.randomUUID());
        when(referralRepository.findById(id)).thenReturn(Optional.of(referral));

        assertThatThrownBy(() -> referralService.claimReferral(id, doctor(doctorId)))
                .isInstanceOf(ConflictException.class);
        verify(referralRepository, never()).save(any());
    }

    // ── assignDoctor (SUPER_ADMIN override) ─────────────────────────────────

    @Test
    void assignDoctor_toValidDoctor_setsAssigneeAndAdvancesStageFromCreated() {
        UUID id = UUID.randomUUID();
        Referral referral = existingReferral(id, ashaId, ReferralStatus.PENDING);
        User doctorUser = new User();
        doctorUser.setRole(Role.DOCTOR);
        when(referralRepository.findById(id)).thenReturn(Optional.of(referral));
        when(userRepository.findById(doctorId)).thenReturn(Optional.of(doctorUser));
        when(referralRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        referralService.assignDoctor(id, doctorId, admin(UUID.randomUUID()));

        assertThat(referral.getAssignedDoctorId()).isEqualTo(doctorId);
        assertThat(referral.getReviewStage()).isEqualTo(ReferralReviewStage.ASSIGNED_TO_DOCTOR);
    }

    @Test
    void assignDoctor_toNonDoctorUser_throwsBadRequest() {
        UUID id = UUID.randomUUID();
        Referral referral = existingReferral(id, ashaId, ReferralStatus.PENDING);
        User ashaUser = new User();
        ashaUser.setRole(Role.ASHA);
        when(referralRepository.findById(id)).thenReturn(Optional.of(referral));
        when(userRepository.findById(ashaId)).thenReturn(Optional.of(ashaUser));

        assertThatThrownBy(() -> referralService.assignDoctor(id, ashaId, admin(UUID.randomUUID())))
                .isInstanceOf(BadRequestException.class);
        verify(referralRepository, never()).save(any());
    }

    @Test
    void assignDoctor_toUnknownUser_throwsBadRequest() {
        UUID id = UUID.randomUUID();
        Referral referral = existingReferral(id, ashaId, ReferralStatus.PENDING);
        UUID unknownId = UUID.randomUUID();
        when(referralRepository.findById(id)).thenReturn(Optional.of(referral));
        when(userRepository.findById(unknownId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> referralService.assignDoctor(id, unknownId, admin(UUID.randomUUID())))
                .isInstanceOf(BadRequestException.class);
    }

    // ── updateReviewStage — forward-only transition guard ───────────────────

    @Test
    void updateReviewStage_legalTransition_succeeds() {
        UUID id = UUID.randomUUID();
        Referral referral = existingReferral(id, ashaId, ReferralStatus.PENDING);
        referral.setAssignedDoctorId(doctorId);
        referral.setReviewStage(ReferralReviewStage.ASSIGNED_TO_DOCTOR);
        when(referralRepository.findById(id)).thenReturn(Optional.of(referral));
        when(referralRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        referralService.updateReviewStage(id, ReferralReviewStage.UNDER_REVIEW, doctor(doctorId));

        assertThat(referral.getReviewStage()).isEqualTo(ReferralReviewStage.UNDER_REVIEW);
    }

    @Test
    void updateReviewStage_skippingAStage_throwsBadRequest() {
        UUID id = UUID.randomUUID();
        Referral referral = existingReferral(id, ashaId, ReferralStatus.PENDING);
        referral.setAssignedDoctorId(doctorId);
        referral.setReviewStage(ReferralReviewStage.ASSIGNED_TO_DOCTOR);
        when(referralRepository.findById(id)).thenReturn(Optional.of(referral));

        assertThatThrownBy(() -> referralService.updateReviewStage(id, ReferralReviewStage.CLOSED, doctor(doctorId)))
                .isInstanceOf(BadRequestException.class);
        verify(referralRepository, never()).save(any());
    }

    @Test
    void updateReviewStage_movingBackward_throwsBadRequest() {
        UUID id = UUID.randomUUID();
        Referral referral = existingReferral(id, ashaId, ReferralStatus.PENDING);
        referral.setAssignedDoctorId(doctorId);
        referral.setReviewStage(ReferralReviewStage.UNDER_REVIEW);
        when(referralRepository.findById(id)).thenReturn(Optional.of(referral));

        assertThatThrownBy(() -> referralService.updateReviewStage(
                id, ReferralReviewStage.ASSIGNED_TO_DOCTOR, doctor(doctorId)))
                .isInstanceOf(BadRequestException.class);
    }

    @Test
    void updateReviewStage_directlyFromCreated_isRejected() {
        // CREATED -> ASSIGNED_TO_DOCTOR is only reachable via claim/assign, never a raw PATCH.
        UUID id = UUID.randomUUID();
        Referral referral = existingReferral(id, ashaId, ReferralStatus.PENDING);
        when(referralRepository.findById(id)).thenReturn(Optional.of(referral));

        assertThatThrownBy(() -> referralService.updateReviewStage(
                id, ReferralReviewStage.ASSIGNED_TO_DOCTOR, admin(UUID.randomUUID())))
                .isInstanceOf(BadRequestException.class);
    }

    @Test
    void updateReviewStage_asNonAssignedDoctor_throwsForbidden() {
        UUID id = UUID.randomUUID();
        Referral referral = existingReferral(id, ashaId, ReferralStatus.PENDING);
        referral.setAssignedDoctorId(UUID.randomUUID());
        referral.setReviewStage(ReferralReviewStage.ASSIGNED_TO_DOCTOR);
        when(referralRepository.findById(id)).thenReturn(Optional.of(referral));

        assertThatThrownBy(() -> referralService.updateReviewStage(id, ReferralReviewStage.UNDER_REVIEW, doctor(doctorId)))
                .isInstanceOf(ForbiddenException.class);
    }

    // ── Clinical notes ───────────────────────────────────────────────────────

    @Test
    void addClinicalNote_savesAndReturnsMappedDto() {
        UUID id = UUID.randomUUID();
        Referral referral = existingReferral(id, ashaId, ReferralStatus.PENDING);
        when(referralRepository.findById(id)).thenReturn(Optional.of(referral));
        when(referralClinicalNoteRepository.save(any(ReferralClinicalNote.class)))
                .thenAnswer(inv -> inv.getArgument(0));
        ReferralClinicalNoteDto expected = ReferralClinicalNoteDto.builder().referralId(id).note("Looks stable").build();
        when(referralClinicalNoteMapper.toDto(any(ReferralClinicalNote.class))).thenReturn(expected);

        ReferralClinicalNoteDto result = referralService.addClinicalNote(id, "Looks stable", doctor(doctorId));

        assertThat(result.getNote()).isEqualTo("Looks stable");
    }

    @Test
    void addClinicalNote_forUnknownReferral_throwsReferralNotFound() {
        UUID id = UUID.randomUUID();
        when(referralRepository.findById(id)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> referralService.addClinicalNote(id, "note", doctor(doctorId)))
                .isInstanceOf(ReferralNotFoundException.class);
    }

    @Test
    void getClinicalNotes_returnsNewestFirstFromRepository() {
        UUID id = UUID.randomUUID();
        when(referralRepository.findById(id)).thenReturn(Optional.of(existingReferral(id, ashaId, ReferralStatus.PENDING)));
        when(referralClinicalNoteRepository.findAllByReferralIdOrderByCreatedAtDesc(id)).thenReturn(List.of());

        referralService.getClinicalNotes(id, doctor(doctorId));

        verify(referralClinicalNoteRepository).findAllByReferralIdOrderByCreatedAtDesc(id);
    }

    // ── Recommendation ───────────────────────────────────────────────────────

    @Test
    void setRecommendation_updatesReferral() {
        UUID id = UUID.randomUUID();
        Referral referral = existingReferral(id, ashaId, ReferralStatus.PENDING);
        when(referralRepository.findById(id)).thenReturn(Optional.of(referral));
        when(referralRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        referralService.setRecommendation(id, "Refer to cardiology", doctor(doctorId));

        assertThat(referral.getDoctorRecommendation()).isEqualTo("Refer to cardiology");
    }
}
