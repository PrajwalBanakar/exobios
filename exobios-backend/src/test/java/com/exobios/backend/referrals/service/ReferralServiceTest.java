package com.exobios.backend.referrals.service;

import com.exobios.backend.assessments.entity.Assessment;
import com.exobios.backend.assessments.entity.enums.AssessmentStatus;
import com.exobios.backend.assessments.exception.AssessmentNotFoundException;
import com.exobios.backend.assessments.repository.AssessmentRepository;
import com.exobios.backend.common.exception.BadRequestException;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.common.exception.ResourceNotFoundException;
import com.exobios.backend.patients.repository.PatientRepository;
import com.exobios.backend.referrals.dto.CreateReferralRequest;
import com.exobios.backend.referrals.dto.ReferralDto;
import com.exobios.backend.referrals.dto.UpdateReferralRequest;
import com.exobios.backend.referrals.entity.Referral;
import com.exobios.backend.referrals.entity.enums.ReferralStatus;
import com.exobios.backend.referrals.exception.ReferralNotFoundException;
import com.exobios.backend.referrals.mapper.ReferralMapper;
import com.exobios.backend.referrals.repository.ReferralRepository;
import com.exobios.backend.security.UserPrincipal;
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

    @Mock private ReferralRepository   referralRepository;
    @Mock private AssessmentRepository assessmentRepository;
    @Mock private PatientRepository    patientRepository;
    @Mock private ReferralMapper       referralMapper;

    private ReferralService referralService;

    private final UUID ashaId    = UUID.randomUUID();
    private final UUID otherAsha = UUID.randomUUID();

    @BeforeEach
    void setUp() {
        referralService = new ReferralService(referralRepository, assessmentRepository, patientRepository, referralMapper);
        lenient().when(referralMapper.toDto(any(Referral.class))).thenAnswer(inv -> {
            Referral r = inv.getArgument(0);
            return ReferralDto.builder().id(r.getId()).ashaWorkerId(r.getAshaWorkerId()).status(r.getStatus()).build();
        });
        lenient().when(referralMapper.toDtoList(org.mockito.ArgumentMatchers.anyList())).thenAnswer(inv -> {
            List<Referral> list = inv.getArgument(0);
            return list.stream().map(r -> ReferralDto.builder().id(r.getId()).ashaWorkerId(r.getAshaWorkerId()).build()).toList();
        });
    }

    private UserPrincipal asha(UUID id)  { return UserPrincipal.fromToken(id.toString(), "9876543210", "ASHA"); }
    private UserPrincipal admin(UUID id) { return UserPrincipal.fromToken(id.toString(), "9000000000", "SUPER_ADMIN"); }

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

        referralService.getReferrals(patientId, null, pageable, asha(ashaId));

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

        referralService.getReferrals(patientId, null, pageable, admin(UUID.randomUUID()));

        verify(referralRepository).findAllByPatientId(patientId, pageable);
    }

    @Test
    void getReferrals_withoutPatientIdFilter_asAsha_scopedByAshaWorkerId() {
        Pageable pageable = PageRequest.of(0, 20);
        when(referralRepository.findAllByAshaWorkerId(ashaId, pageable)).thenReturn(new PageImpl<>(List.of()));

        referralService.getReferrals(null, null, pageable, asha(ashaId));

        verify(referralRepository).findAllByAshaWorkerId(ashaId, pageable);
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
}
