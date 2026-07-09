package com.exobios.backend.assessments.service;

import com.exobios.backend.assessments.dto.AssessmentDto;
import com.exobios.backend.assessments.dto.CreateAssessmentRequest;
import com.exobios.backend.assessments.dto.UpdateAssessmentRequest;
import com.exobios.backend.assessments.dto.VitalsRequest;
import com.exobios.backend.assessments.entity.Assessment;
import com.exobios.backend.assessments.entity.enums.AssessmentStatus;
import com.exobios.backend.assessments.entity.enums.RiskLevel;
import com.exobios.backend.assessments.exception.AssessmentNotFoundException;
import com.exobios.backend.assessments.mapper.AssessmentMapper;
import com.exobios.backend.assessments.repository.AssessmentRepository;
import com.exobios.backend.common.exception.BadRequestException;
import com.exobios.backend.common.exception.ConflictException;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.common.exception.ResourceNotFoundException;
import com.exobios.backend.integration.ai.AiGateway;
import com.exobios.backend.integration.ai.AiResponse;
import com.exobios.backend.assessments.entity.enums.AiResultStatus;
import com.exobios.backend.patients.entity.Patient;
import com.exobios.backend.patients.repository.PatientRepository;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.users.entity.User;
import com.exobios.backend.users.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.test.util.ReflectionTestUtils;

import java.math.BigDecimal;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AssessmentServiceTest {

    @Mock private AssessmentRepository assessmentRepository;
    @Mock private PatientRepository    patientRepository;
    @Mock private UserRepository       userRepository;
    @Mock private AssessmentMapper     assessmentMapper;
    @Mock private AiGateway            aiGateway;

    private AssessmentService assessmentService;

    private final UUID ashaId    = UUID.randomUUID();
    private final UUID otherAsha = UUID.randomUUID();

    @BeforeEach
    void setUp() {
        assessmentService = new AssessmentService(assessmentRepository, patientRepository, userRepository, assessmentMapper, aiGateway);
        lenient().when(assessmentMapper.toDto(any(Assessment.class))).thenAnswer(inv -> {
            Assessment a = inv.getArgument(0);
            return AssessmentDto.builder().id(a.getId()).assessmentNumber(a.getAssessmentNumber())
                    .ashaWorkerId(a.getAshaWorkerId()).status(a.getStatus()).riskLevel(a.getRiskLevel()).build();
        });
    }

    private UserPrincipal asha(UUID id)  { return UserPrincipal.fromToken(id.toString(), "9876543210", "ASHA"); }
    private UserPrincipal admin(UUID id) { return UserPrincipal.fromToken(id.toString(), "9000000000", "SUPER_ADMIN"); }

    private Patient patientOwnedBy(UUID owner) {
        Patient p = new Patient();
        ReflectionTestUtils.setField(p, "id", UUID.randomUUID());
        p.setAshaWorkerId(owner);
        return p;
    }

    private Assessment existingAssessment(UUID id, UUID owner, AssessmentStatus status) {
        Assessment a = new Assessment();
        ReflectionTestUtils.setField(a, "id", id);
        a.setAssessmentNumber("ASMT-2026-000001");
        a.setPatientId(UUID.randomUUID());
        a.setAshaWorkerId(owner);
        a.setStatus(status);
        return a;
    }

    // ── createAssessment — ownership resolution ─────────────────────────────────

    @Test
    void createAssessment_asAsha_forOwnPatient_succeeds() {
        Patient patient = patientOwnedBy(ashaId);
        CreateAssessmentRequest req = new CreateAssessmentRequest();
        req.setPatientId(patient.getId());
        when(patientRepository.findById(patient.getId())).thenReturn(Optional.of(patient));
        when(assessmentRepository.findMaxSequenceByYearPrefix(anyString())).thenReturn(0);
        when(assessmentRepository.saveAndFlush(any())).thenAnswer(inv -> inv.getArgument(0));

        AssessmentDto result = assessmentService.createAssessment(req, asha(ashaId));

        assertThat(result.getAshaWorkerId()).isEqualTo(ashaId);
    }

    @Test
    void createAssessment_asAsha_forAnotherAshasPatient_throwsForbidden() {
        Patient patient = patientOwnedBy(otherAsha);
        CreateAssessmentRequest req = new CreateAssessmentRequest();
        req.setPatientId(patient.getId());
        when(patientRepository.findById(patient.getId())).thenReturn(Optional.of(patient));

        assertThatThrownBy(() -> assessmentService.createAssessment(req, asha(ashaId)))
                .isInstanceOf(ForbiddenException.class);
        verify(assessmentRepository, never()).saveAndFlush(any());
    }

    @Test
    void createAssessment_forUnknownPatient_throwsResourceNotFound() {
        UUID patientId = UUID.randomUUID();
        CreateAssessmentRequest req = new CreateAssessmentRequest();
        req.setPatientId(patientId);
        when(patientRepository.findById(patientId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> assessmentService.createAssessment(req, asha(ashaId)))
                .isInstanceOf(ResourceNotFoundException.class);
    }

    @Test
    void createAssessment_asSuperAdmin_withoutAshaWorkerId_inheritsFromPatient() {
        Patient patient = patientOwnedBy(otherAsha);
        CreateAssessmentRequest req = new CreateAssessmentRequest();
        req.setPatientId(patient.getId());
        when(patientRepository.findById(patient.getId())).thenReturn(Optional.of(patient));
        when(assessmentRepository.findMaxSequenceByYearPrefix(anyString())).thenReturn(0);
        when(assessmentRepository.saveAndFlush(any())).thenAnswer(inv -> inv.getArgument(0));

        AssessmentDto result = assessmentService.createAssessment(req, admin(UUID.randomUUID()));

        assertThat(result.getAshaWorkerId()).isEqualTo(otherAsha);
    }

    @Test
    void createAssessment_asSuperAdmin_withNonexistentAshaWorkerId_throwsResourceNotFound() {
        Patient patient = patientOwnedBy(otherAsha);
        UUID bogusAsha = UUID.randomUUID();
        CreateAssessmentRequest req = new CreateAssessmentRequest();
        req.setPatientId(patient.getId());
        req.setAshaWorkerId(bogusAsha);
        when(patientRepository.findById(patient.getId())).thenReturn(Optional.of(patient));
        when(userRepository.findById(bogusAsha)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> assessmentService.createAssessment(req, admin(UUID.randomUUID())))
                .isInstanceOf(ResourceNotFoundException.class);
    }

    @Test
    void createAssessment_retriesOnNumberCollisionAndSucceeds() {
        Patient patient = patientOwnedBy(ashaId);
        CreateAssessmentRequest req = new CreateAssessmentRequest();
        req.setPatientId(patient.getId());
        when(patientRepository.findById(patient.getId())).thenReturn(Optional.of(patient));
        when(assessmentRepository.findMaxSequenceByYearPrefix(anyString())).thenReturn(0);
        when(assessmentRepository.saveAndFlush(any()))
                .thenThrow(new DataIntegrityViolationException("duplicate assessment_number"))
                .thenAnswer(inv -> inv.getArgument(0));

        assessmentService.createAssessment(req, asha(ashaId));

        verify(assessmentRepository, times(2)).saveAndFlush(any());
    }

    @Test
    void createAssessment_throwsConflictAfterExhaustingRetries() {
        Patient patient = patientOwnedBy(ashaId);
        CreateAssessmentRequest req = new CreateAssessmentRequest();
        req.setPatientId(patient.getId());
        when(patientRepository.findById(patient.getId())).thenReturn(Optional.of(patient));
        when(assessmentRepository.findMaxSequenceByYearPrefix(anyString())).thenReturn(0);
        when(assessmentRepository.saveAndFlush(any()))
                .thenThrow(new DataIntegrityViolationException("duplicate"));

        assertThatThrownBy(() -> assessmentService.createAssessment(req, asha(ashaId)))
                .isInstanceOf(ConflictException.class);
        verify(assessmentRepository, times(3)).saveAndFlush(any());
    }

    // ── submitAssessment — state transition + AI mirroring ──────────────────────

    @Test
    void submitAssessment_fromDraft_transitionsToSubmittedAndMirrorsRiskLevel() {
        UUID id = UUID.randomUUID();
        Assessment assessment = existingAssessment(id, ashaId, AssessmentStatus.DRAFT);
        when(assessmentRepository.findById(id)).thenReturn(Optional.of(assessment));
        when(assessmentRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));
        AiResponse aiResponse = AiResponse.builder()
                .status(AiResultStatus.COMPLETED).riskLevel(RiskLevel.HIGH)
                .confidenceScore(BigDecimal.valueOf(0.9)).build();
        when(aiGateway.analyzeAssessment(any())).thenReturn(aiResponse);

        AssessmentDto result = assessmentService.submitAssessment(id, asha(ashaId));

        assertThat(assessment.getStatus()).isEqualTo(AssessmentStatus.SUBMITTED);
        assertThat(assessment.getSubmittedAt()).isNotNull();
        // Regression guard for the earlier bug where assessments.risk_level was never
        // set even though every Analytics query filters/aggregates on that column.
        assertThat(assessment.getRiskLevel()).isEqualTo(RiskLevel.HIGH);
        assertThat(result.getRiskLevel()).isEqualTo(RiskLevel.HIGH);
    }

    @Test
    void submitAssessment_whenAiGatewayFails_fallsBackToPlaceholderInsteadOfThrowing() {
        UUID id = UUID.randomUUID();
        Assessment assessment = existingAssessment(id, ashaId, AssessmentStatus.DRAFT);
        when(assessmentRepository.findById(id)).thenReturn(Optional.of(assessment));
        when(assessmentRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));
        when(aiGateway.analyzeAssessment(any())).thenThrow(new RuntimeException("AI service unreachable"));

        assessmentService.submitAssessment(id, asha(ashaId));

        assertThat(assessment.getStatus()).isEqualTo(AssessmentStatus.SUBMITTED);
        assertThat(assessment.getAiResult()).isNotNull();
        assertThat(assessment.getAiResult().getStatus()).isEqualTo(AiResultStatus.PENDING);
    }

    @Test
    void submitAssessment_onAlreadySubmittedAssessment_throwsBadRequest() {
        UUID id = UUID.randomUUID();
        Assessment assessment = existingAssessment(id, ashaId, AssessmentStatus.SUBMITTED);
        when(assessmentRepository.findById(id)).thenReturn(Optional.of(assessment));

        assertThatThrownBy(() -> assessmentService.submitAssessment(id, asha(ashaId)))
                .isInstanceOf(BadRequestException.class);
        verify(assessmentRepository, never()).save(any());
    }

    @Test
    void submitAssessment_asNonOwningAsha_throwsForbidden() {
        UUID id = UUID.randomUUID();
        Assessment assessment = existingAssessment(id, otherAsha, AssessmentStatus.DRAFT);
        when(assessmentRepository.findById(id)).thenReturn(Optional.of(assessment));

        assertThatThrownBy(() -> assessmentService.submitAssessment(id, asha(ashaId)))
                .isInstanceOf(ForbiddenException.class);
    }

    @Test
    void submitAssessment_unknownId_throwsAssessmentNotFound() {
        UUID id = UUID.randomUUID();
        when(assessmentRepository.findById(id)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> assessmentService.submitAssessment(id, asha(ashaId)))
                .isInstanceOf(AssessmentNotFoundException.class);
    }

    // ── updateAssessment — DRAFT-only mutability ────────────────────────────────

    @Test
    void updateAssessment_onSubmittedAssessment_throwsBadRequest() {
        UUID id = UUID.randomUUID();
        Assessment assessment = existingAssessment(id, ashaId, AssessmentStatus.SUBMITTED);
        when(assessmentRepository.findById(id)).thenReturn(Optional.of(assessment));
        UpdateAssessmentRequest req = new UpdateAssessmentRequest();
        req.setPatientComplaint("Updated");

        assertThatThrownBy(() -> assessmentService.updateAssessment(id, req, asha(ashaId)))
                .isInstanceOf(BadRequestException.class);
    }

    @Test
    void updateAssessment_onDraft_appliesPartialUpdate() {
        UUID id = UUID.randomUUID();
        Assessment assessment = existingAssessment(id, ashaId, AssessmentStatus.DRAFT);
        when(assessmentRepository.findById(id)).thenReturn(Optional.of(assessment));
        when(assessmentRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));
        UpdateAssessmentRequest req = new UpdateAssessmentRequest();
        req.setPatientComplaint("Severe headache");

        assessmentService.updateAssessment(id, req, asha(ashaId));

        assertThat(assessment.getPatientComplaint()).isEqualTo("Severe headache");
    }

    @Test
    void updateAssessment_computesBmiFromHeightAndWeightWhenNotProvided() {
        UUID id = UUID.randomUUID();
        Assessment assessment = existingAssessment(id, ashaId, AssessmentStatus.DRAFT);
        when(assessmentRepository.findById(id)).thenReturn(Optional.of(assessment));
        when(assessmentRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        UpdateAssessmentRequest req = new UpdateAssessmentRequest();
        VitalsRequest vitals = new VitalsRequest();
        vitals.setHeight(BigDecimal.valueOf(170));
        vitals.setWeight(BigDecimal.valueOf(70));
        req.setVitals(vitals);

        assessmentService.updateAssessment(id, req, asha(ashaId));

        // 70 / (1.70^2) ≈ 24.22
        assertThat(assessment.getVitals().getBmi()).isEqualByComparingTo("24.22");
    }

    // ── getPatientAssessments — ownership-scoped listing ────────────────────────

    @Test
    void getPatientAssessments_forUnknownPatient_throwsResourceNotFound() {
        UUID patientId = UUID.randomUUID();
        when(patientRepository.findById(patientId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> assessmentService.getPatientAssessments(
                patientId, org.springframework.data.domain.PageRequest.of(0, 20), asha(ashaId)))
                .isInstanceOf(ResourceNotFoundException.class);
    }
}
