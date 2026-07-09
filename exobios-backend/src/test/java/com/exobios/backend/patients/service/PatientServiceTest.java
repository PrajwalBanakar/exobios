package com.exobios.backend.patients.service;

import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.common.exception.BadRequestException;
import com.exobios.backend.common.exception.ConflictException;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.common.exception.ResourceNotFoundException;
import com.exobios.backend.patients.dto.CreatePatientRequest;
import com.exobios.backend.patients.dto.PatientDto;
import com.exobios.backend.patients.dto.UpdatePatientRequest;
import com.exobios.backend.patients.entity.Patient;
import com.exobios.backend.patients.entity.enums.Gender;
import com.exobios.backend.patients.entity.enums.PatientStatus;
import com.exobios.backend.patients.exception.PatientNotFoundException;
import com.exobios.backend.patients.mapper.PatientMapper;
import com.exobios.backend.patients.repository.PatientRepository;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.users.entity.User;
import com.exobios.backend.users.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.dao.DataIntegrityViolationException;
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
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class PatientServiceTest {

    @Mock private PatientRepository patientRepository;
    @Mock private PatientMapper     patientMapper;
    @Mock private UserRepository    userRepository;

    private PatientService patientService;

    private final UUID ashaId    = UUID.randomUUID();
    private final UUID otherAsha = UUID.randomUUID();

    @BeforeEach
    void setUp() {
        patientService = new PatientService(patientRepository, patientMapper, userRepository);
        // toDto() is called on every success path but not on the forbidden/not-found paths —
        // lenient() avoids Mockito's strict-stubbing check failing on tests that never reach it.
        org.mockito.Mockito.lenient().when(patientMapper.toDto(any(Patient.class))).thenAnswer(inv -> {
            Patient p = inv.getArgument(0);
            return PatientDto.builder().id(p.getId()).name(p.getName()).ashaWorkerId(p.getAshaWorkerId()).build();
        });
    }

    private UserPrincipal asha(UUID id)  { return UserPrincipal.fromToken(id.toString(), "9876543210", "ASHA"); }
    private UserPrincipal admin(UUID id) { return UserPrincipal.fromToken(id.toString(), "9000000000", "SUPER_ADMIN"); }

    private Patient existingPatient(UUID id, UUID owner) {
        Patient p = new Patient();
        ReflectionTestUtils.setField(p, "id", id);
        p.setName("Priya Sharma");
        p.setAshaWorkerId(owner);
        p.setStatus(PatientStatus.ACTIVE);
        return p;
    }

    private CreatePatientRequest createRequest() {
        CreatePatientRequest req = new CreatePatientRequest();
        req.setName("Priya Sharma");
        req.setGender(Gender.FEMALE);
        req.setAge(28);
        return req;
    }

    // ── createPatient — ownership resolution ────────────────────────────────────

    @Test
    void createPatient_asAsha_ignoresRequestedAshaWorkerIdAndUsesOwnId() {
        CreatePatientRequest req = createRequest();
        req.setAshaWorkerId(UUID.randomUUID()); // must be ignored — ASHA can only create under themselves
        when(patientRepository.findMaxSequenceByYearPrefix(anyString())).thenReturn(0);
        when(patientRepository.saveAndFlush(any())).thenAnswer(inv -> inv.getArgument(0));

        patientService.createPatient(req, asha(ashaId));

        var captor = org.mockito.ArgumentCaptor.forClass(Patient.class);
        verify(patientRepository).saveAndFlush(captor.capture());
        assertThat(captor.getValue().getAshaWorkerId()).isEqualTo(ashaId);
    }

    @Test
    void createPatient_asSuperAdmin_withoutAshaWorkerId_throwsBadRequest() {
        CreatePatientRequest req = createRequest(); // ashaWorkerId left null

        assertThatThrownBy(() -> patientService.createPatient(req, admin(UUID.randomUUID())))
                .isInstanceOf(BadRequestException.class);
        verify(patientRepository, never()).saveAndFlush(any());
    }

    @Test
    void createPatient_asSuperAdmin_withNonexistentAshaWorkerId_throwsResourceNotFound() {
        UUID bogusAsha = UUID.randomUUID();
        CreatePatientRequest req = createRequest();
        req.setAshaWorkerId(bogusAsha);
        when(userRepository.findById(bogusAsha)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> patientService.createPatient(req, admin(UUID.randomUUID())))
                .isInstanceOf(ResourceNotFoundException.class);
    }

    @Test
    void createPatient_asSuperAdmin_withValidAshaWorkerId_succeeds() {
        UUID targetAsha = UUID.randomUUID();
        CreatePatientRequest req = createRequest();
        req.setAshaWorkerId(targetAsha);
        when(userRepository.findById(targetAsha)).thenReturn(Optional.of(new User()));
        when(patientRepository.findMaxSequenceByYearPrefix(anyString())).thenReturn(0);
        when(patientRepository.saveAndFlush(any())).thenAnswer(inv -> inv.getArgument(0));

        PatientDto result = patientService.createPatient(req, admin(UUID.randomUUID()));

        assertThat(result.getAshaWorkerId()).isEqualTo(targetAsha);
    }

    // ── createPatient — sequence-collision retry ────────────────────────────────

    @Test
    void createPatient_retriesOnCodeCollisionAndSucceedsOnSecondAttempt() {
        CreatePatientRequest req = createRequest();
        when(patientRepository.findMaxSequenceByYearPrefix(anyString())).thenReturn(0);
        when(patientRepository.saveAndFlush(any()))
                .thenThrow(new DataIntegrityViolationException("duplicate patient_code"))
                .thenAnswer(inv -> inv.getArgument(0));

        patientService.createPatient(req, asha(ashaId));

        verify(patientRepository, times(2)).saveAndFlush(any());
    }

    @Test
    void createPatient_throwsConflictAfterExhaustingAllRetries() {
        CreatePatientRequest req = createRequest();
        when(patientRepository.findMaxSequenceByYearPrefix(anyString())).thenReturn(0);
        when(patientRepository.saveAndFlush(any()))
                .thenThrow(new DataIntegrityViolationException("duplicate patient_code"));

        assertThatThrownBy(() -> patientService.createPatient(req, asha(ashaId)))
                .isInstanceOf(ConflictException.class);
        verify(patientRepository, times(3)).saveAndFlush(any());
    }

    // ── getPatientById — ownership ───────────────────────────────────────────────

    @Test
    void getPatientById_asOwningAsha_succeeds() {
        UUID patientId = UUID.randomUUID();
        when(patientRepository.findById(patientId)).thenReturn(Optional.of(existingPatient(patientId, ashaId)));

        PatientDto result = patientService.getPatientById(patientId, asha(ashaId));

        assertThat(result.getId()).isEqualTo(patientId);
    }

    @Test
    void getPatientById_asNonOwningAsha_throwsForbidden() {
        UUID patientId = UUID.randomUUID();
        when(patientRepository.findById(patientId)).thenReturn(Optional.of(existingPatient(patientId, otherAsha)));

        assertThatThrownBy(() -> patientService.getPatientById(patientId, asha(ashaId)))
                .isInstanceOf(ForbiddenException.class);
    }

    @Test
    void getPatientById_asSuperAdmin_canAccessAnyPatient() {
        UUID patientId = UUID.randomUUID();
        when(patientRepository.findById(patientId)).thenReturn(Optional.of(existingPatient(patientId, otherAsha)));

        PatientDto result = patientService.getPatientById(patientId, admin(UUID.randomUUID()));

        assertThat(result.getId()).isEqualTo(patientId);
    }

    @Test
    void getPatientById_withUnknownId_throwsPatientNotFound() {
        UUID patientId = UUID.randomUUID();
        when(patientRepository.findById(patientId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> patientService.getPatientById(patientId, asha(ashaId)))
                .isInstanceOf(PatientNotFoundException.class);
    }

    // ── getAllPatients — search/scope routing ───────────────────────────────────

    @Test
    void getAllPatients_asAshaWithSearchTerm_usesScopedSearchQuery() {
        Pageable pageable = PageRequest.of(0, 20);
        Page<Patient> page = new PageImpl<>(List.of());
        when(patientRepository.searchByAshaWorkerAndText(any(), any(), any())).thenReturn(page);

        patientService.getAllPatients("priya", pageable, asha(ashaId));

        verify(patientRepository).searchByAshaWorkerAndText(ashaId, "priya", pageable);
        verify(patientRepository, never()).searchByText(any(), any());
        verify(patientRepository, never()).findAll(any(Pageable.class));
    }

    @Test
    void getAllPatients_asAshaWithoutSearchTerm_usesScopedListQuery() {
        Pageable pageable = PageRequest.of(0, 20);
        when(patientRepository.findAllByAshaWorkerId(any(), any())).thenReturn(new PageImpl<>(List.of()));

        patientService.getAllPatients(null, pageable, asha(ashaId));

        verify(patientRepository).findAllByAshaWorkerId(ashaId, pageable);
    }

    @Test
    void getAllPatients_asSuperAdminWithSearchTerm_searchesAcrossAllPatients() {
        Pageable pageable = PageRequest.of(0, 20);
        when(patientRepository.searchByText(any(), any())).thenReturn(new PageImpl<>(List.of()));

        patientService.getAllPatients("priya", pageable, admin(UUID.randomUUID()));

        verify(patientRepository).searchByText("priya", pageable);
        verify(patientRepository, never()).searchByAshaWorkerAndText(any(), any(), any());
    }

    @Test
    void getAllPatients_asSuperAdminWithoutSearchTerm_returnsAllPatients() {
        Pageable pageable = PageRequest.of(0, 20);
        when(patientRepository.findAll(pageable)).thenReturn(new PageImpl<>(List.of()));

        PageResponse<PatientDto> result = patientService.getAllPatients("  ", pageable, admin(UUID.randomUUID()));

        assertThat(result).isNotNull();
        verify(patientRepository).findAll(pageable);
    }

    // ── updatePatient / changeStatus — ownership ────────────────────────────────

    @Test
    void updatePatient_asNonOwningAsha_throwsForbidden() {
        UUID patientId = UUID.randomUUID();
        when(patientRepository.findById(patientId)).thenReturn(Optional.of(existingPatient(patientId, otherAsha)));
        UpdatePatientRequest req = new UpdatePatientRequest();
        req.setName("New Name");

        assertThatThrownBy(() -> patientService.updatePatient(patientId, req, asha(ashaId)))
                .isInstanceOf(ForbiddenException.class);
        verify(patientRepository, never()).save(any());
    }

    @Test
    void changeStatus_asOwningAsha_updatesStatus() {
        UUID patientId = UUID.randomUUID();
        Patient patient = existingPatient(patientId, ashaId);
        when(patientRepository.findById(patientId)).thenReturn(Optional.of(patient));
        when(patientRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        patientService.changeStatus(patientId, PatientStatus.DECEASED, asha(ashaId));

        assertThat(patient.getStatus()).isEqualTo(PatientStatus.DECEASED);
    }

    @Test
    void changeStatus_asNonOwningAsha_throwsForbiddenAndDoesNotMutate() {
        UUID patientId = UUID.randomUUID();
        Patient patient = existingPatient(patientId, otherAsha);
        when(patientRepository.findById(patientId)).thenReturn(Optional.of(patient));

        assertThatThrownBy(() -> patientService.changeStatus(patientId, PatientStatus.DECEASED, asha(ashaId)))
                .isInstanceOf(ForbiddenException.class);
        assertThat(patient.getStatus()).isEqualTo(PatientStatus.ACTIVE);
        verify(patientRepository, never()).save(any());
    }
}
