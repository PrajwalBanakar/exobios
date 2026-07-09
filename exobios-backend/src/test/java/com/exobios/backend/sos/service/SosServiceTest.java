package com.exobios.backend.sos.service;

import com.exobios.backend.assessments.repository.AssessmentRepository;
import com.exobios.backend.common.exception.BadRequestException;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.common.exception.ResourceNotFoundException;
import com.exobios.backend.patients.repository.PatientRepository;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.sos.dto.CreateSosRequest;
import com.exobios.backend.sos.dto.SosRecordDto;
import com.exobios.backend.sos.entity.SosRecord;
import com.exobios.backend.sos.entity.enums.SosStatus;
import com.exobios.backend.sos.entity.enums.SosType;
import com.exobios.backend.sos.exception.SosRecordNotFoundException;
import com.exobios.backend.sos.mapper.SosMapper;
import com.exobios.backend.sos.repository.SosRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

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
class SosServiceTest {

    @Mock private SosRepository        sosRepository;
    @Mock private SosMapper            sosMapper;
    @Mock private PatientRepository    patientRepository;
    @Mock private AssessmentRepository assessmentRepository;

    private SosService sosService;

    private final UUID ashaId    = UUID.randomUUID();
    private final UUID otherAsha = UUID.randomUUID();

    @BeforeEach
    void setUp() {
        sosService = new SosService(sosRepository, sosMapper, patientRepository, assessmentRepository);
        lenient().when(sosMapper.toDto(any(SosRecord.class))).thenAnswer(inv -> {
            SosRecord s = inv.getArgument(0);
            return SosRecordDto.builder().id(s.getId()).ashaWorkerId(s.getAshaWorkerId()).status(s.getStatus()).build();
        });
    }

    private UserPrincipal asha(UUID id)  { return UserPrincipal.fromToken(id.toString(), "9876543210", "ASHA"); }
    private UserPrincipal admin(UUID id) { return UserPrincipal.fromToken(id.toString(), "9000000000", "SUPER_ADMIN"); }

    private CreateSosRequest validRequest() {
        CreateSosRequest req = new CreateSosRequest();
        req.setPatientId(UUID.randomUUID());
        req.setType(SosType.MEDICAL_EMERGENCY);
        return req;
    }

    private SosRecord existingSos(UUID id, UUID owner, SosStatus status) {
        SosRecord s = new SosRecord();
        ReflectionTestUtils.setField(s, "id", id);
        s.setPatientId(UUID.randomUUID());
        s.setAshaWorkerId(owner);
        s.setType(SosType.MEDICAL_EMERGENCY);
        s.setStatus(status);
        return s;
    }

    // ── createSos — existence checks ────────────────────────────────────────────

    @Test
    void createSos_forUnknownPatient_throwsResourceNotFound() {
        CreateSosRequest req = validRequest();
        when(patientRepository.existsById(req.getPatientId())).thenReturn(false);

        assertThatThrownBy(() -> sosService.createSos(req, asha(ashaId)))
                .isInstanceOf(ResourceNotFoundException.class);
        verify(sosRepository, never()).save(any());
    }

    @Test
    void createSos_withUnknownAssessmentId_throwsResourceNotFound() {
        CreateSosRequest req = validRequest();
        req.setAssessmentId(UUID.randomUUID());
        when(patientRepository.existsById(req.getPatientId())).thenReturn(true);
        when(assessmentRepository.existsById(req.getAssessmentId())).thenReturn(false);

        assertThatThrownBy(() -> sosService.createSos(req, asha(ashaId)))
                .isInstanceOf(ResourceNotFoundException.class);
    }

    @Test
    void createSos_withoutAssessmentId_skipsAssessmentCheck() {
        CreateSosRequest req = validRequest(); // assessmentId left null
        when(patientRepository.existsById(req.getPatientId())).thenReturn(true);
        when(sosRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        sosService.createSos(req, asha(ashaId));

        verify(assessmentRepository, never()).existsById(any());
    }

    @Test
    void createSos_setsAshaWorkerFromPrincipalAndStatusActive() {
        CreateSosRequest req = validRequest();
        when(patientRepository.existsById(req.getPatientId())).thenReturn(true);
        when(sosRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        SosRecordDto result = sosService.createSos(req, asha(ashaId));

        assertThat(result.getAshaWorkerId()).isEqualTo(ashaId);
        assertThat(result.getStatus()).isEqualTo(SosStatus.ACTIVE);
    }

    // ── updateSosStatus — SUPER_ADMIN unrestricted, ASHA self-cancel-only ───────

    @Test
    void updateSosStatus_asSuperAdmin_canSetAnyStatus() {
        UUID id = UUID.randomUUID();
        SosRecord sos = existingSos(id, otherAsha, SosStatus.ACTIVE);
        when(sosRepository.findById(id)).thenReturn(Optional.of(sos));
        when(sosRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        sosService.updateSosStatus(id, SosStatus.RESOLVED, admin(UUID.randomUUID()));

        assertThat(sos.getStatus()).isEqualTo(SosStatus.RESOLVED);
        assertThat(sos.getResolvedAt()).isNotNull();
    }

    @Test
    void updateSosStatus_asNonOwningAsha_throwsForbidden() {
        UUID id = UUID.randomUUID();
        when(sosRepository.findById(id)).thenReturn(Optional.of(existingSos(id, otherAsha, SosStatus.ACTIVE)));

        assertThatThrownBy(() -> sosService.updateSosStatus(id, SosStatus.CANCELLED, asha(ashaId)))
                .isInstanceOf(ForbiddenException.class);
    }

    @Test
    void updateSosStatus_asOwningAsha_requestingNonCancelStatus_throwsForbidden() {
        UUID id = UUID.randomUUID();
        when(sosRepository.findById(id)).thenReturn(Optional.of(existingSos(id, ashaId, SosStatus.ACTIVE)));

        assertThatThrownBy(() -> sosService.updateSosStatus(id, SosStatus.RESOLVED, asha(ashaId)))
                .isInstanceOf(ForbiddenException.class);
    }

    @Test
    void updateSosStatus_asOwningAsha_cancellingNonActiveRecord_throwsBadRequest() {
        UUID id = UUID.randomUUID();
        when(sosRepository.findById(id)).thenReturn(Optional.of(existingSos(id, ashaId, SosStatus.RESOLVED)));

        assertThatThrownBy(() -> sosService.updateSosStatus(id, SosStatus.CANCELLED, asha(ashaId)))
                .isInstanceOf(BadRequestException.class);
    }

    @Test
    void updateSosStatus_asOwningAsha_cancellingActiveRecord_succeeds() {
        UUID id = UUID.randomUUID();
        SosRecord sos = existingSos(id, ashaId, SosStatus.ACTIVE);
        when(sosRepository.findById(id)).thenReturn(Optional.of(sos));
        when(sosRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        sosService.updateSosStatus(id, SosStatus.CANCELLED, asha(ashaId));

        assertThat(sos.getStatus()).isEqualTo(SosStatus.CANCELLED);
    }

    @Test
    void updateSosStatus_unknownId_throwsSosRecordNotFound() {
        UUID id = UUID.randomUUID();
        when(sosRepository.findById(id)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> sosService.updateSosStatus(id, SosStatus.RESOLVED, admin(UUID.randomUUID())))
                .isInstanceOf(SosRecordNotFoundException.class);
    }

    // ── getSosById — ownership ───────────────────────────────────────────────────

    @Test
    void getSosById_asNonOwningAsha_throwsForbidden() {
        UUID id = UUID.randomUUID();
        when(sosRepository.findById(id)).thenReturn(Optional.of(existingSos(id, otherAsha, SosStatus.ACTIVE)));

        assertThatThrownBy(() -> sosService.getSosById(id, asha(ashaId)))
                .isInstanceOf(ForbiddenException.class);
    }

    @Test
    void getSosById_asSuperAdmin_canAccessAnyRecord() {
        UUID id = UUID.randomUUID();
        when(sosRepository.findById(id)).thenReturn(Optional.of(existingSos(id, otherAsha, SosStatus.ACTIVE)));

        SosRecordDto result = sosService.getSosById(id, admin(UUID.randomUUID()));

        assertThat(result.getId()).isEqualTo(id);
    }
}
