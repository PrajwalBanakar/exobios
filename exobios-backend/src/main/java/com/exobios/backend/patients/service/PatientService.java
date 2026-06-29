package com.exobios.backend.patients.service;

import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.common.exception.BadRequestException;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.common.exception.ResourceNotFoundException;
import com.exobios.backend.patients.dto.CreatePatientRequest;
import com.exobios.backend.patients.dto.PatientDto;
import com.exobios.backend.patients.dto.UpdatePatientRequest;
import com.exobios.backend.patients.entity.Patient;
import com.exobios.backend.patients.entity.enums.PatientStatus;
import com.exobios.backend.patients.exception.PatientNotFoundException;
import com.exobios.backend.patients.mapper.PatientMapper;
import com.exobios.backend.patients.repository.PatientRepository;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.users.entity.enums.Role;
import com.exobios.backend.users.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.Year;
import java.util.UUID;

@Slf4j
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class PatientService {

    private final PatientRepository patientRepository;
    private final PatientMapper     patientMapper;
    private final UserRepository    userRepository;

    @Transactional
    public PatientDto createPatient(CreatePatientRequest request, UserPrincipal principal) {
        UUID ashaWorkerId = resolveAshaWorkerId(request, principal);

        Patient patient = new Patient();
        patient.setPatientCode(generatePatientCode());
        patient.setName(request.getName());
        patient.setAge(request.getAge() != null ? request.getAge().shortValue() : null);
        patient.setGender(request.getGender());
        patient.setDob(request.getDob());
        patient.setPhone(request.getPhone());
        patient.setAddress(request.getAddress());
        patient.setVillage(request.getVillage());
        patient.setDistrict(request.getDistrict());
        patient.setState(request.getState());
        patient.setAadhaarNumber(request.getAadhaarNumber());
        patient.setAshaWorkerId(ashaWorkerId);
        patient.setStatus(PatientStatus.ACTIVE);

        Patient saved = patientRepository.save(patient);
        log.info("Created patient code={} ashaWorker={}", saved.getPatientCode(), ashaWorkerId);
        return patientMapper.toDto(saved);
    }

    public PatientDto getPatientById(UUID id, UserPrincipal principal) {
        Patient patient = findOrThrow(id);
        assertOwnership(patient, principal);
        return patientMapper.toDto(patient);
    }

    public PageResponse<PatientDto> getAllPatients(String search, Pageable pageable,
                                                   UserPrincipal principal) {
        UUID   ashaWorkerId   = isAsha(principal) ? principal.getId() : null;
        String effectiveSearch = StringUtils.hasText(search) ? search.trim() : null;

        Page<Patient> page;
        if (effectiveSearch != null && ashaWorkerId != null) {
            page = patientRepository.searchByAshaWorkerAndText(ashaWorkerId, effectiveSearch, pageable);
        } else if (effectiveSearch != null) {
            page = patientRepository.searchByText(effectiveSearch, pageable);
        } else if (ashaWorkerId != null) {
            page = patientRepository.findAllByAshaWorkerId(ashaWorkerId, pageable);
        } else {
            page = patientRepository.findAll(pageable);
        }
        return PageResponse.of(page.map(patientMapper::toDto));
    }

    @Transactional
    public PatientDto updatePatient(UUID id, UpdatePatientRequest request, UserPrincipal principal) {
        Patient patient = findOrThrow(id);
        assertOwnership(patient, principal);

        patient.setName(request.getName());
        patient.setAge(request.getAge() != null ? request.getAge().shortValue() : null);
        patient.setGender(request.getGender());
        patient.setDob(request.getDob());
        patient.setPhone(request.getPhone());
        patient.setAddress(request.getAddress());
        patient.setVillage(request.getVillage());
        patient.setDistrict(request.getDistrict());
        patient.setState(request.getState());
        if (request.getAadhaarNumber() != null) {
            patient.setAadhaarNumber(StringUtils.hasText(request.getAadhaarNumber())
                    ? request.getAadhaarNumber() : null);
        }

        return patientMapper.toDto(patientRepository.save(patient));
    }

    @Transactional
    public PatientDto changeStatus(UUID id, PatientStatus status, UserPrincipal principal) {
        Patient patient = findOrThrow(id);
        assertOwnership(patient, principal);
        patient.setStatus(status);
        log.info("Changed patient id={} status to {}", id, status);
        return patientMapper.toDto(patientRepository.save(patient));
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private UUID resolveAshaWorkerId(CreatePatientRequest request, UserPrincipal principal) {
        if (isAsha(principal)) {
            return principal.getId();
        }
        // SUPER_ADMIN must specify whose patient this is
        if (request.getAshaWorkerId() == null) {
            throw new BadRequestException("ashaWorkerId is required when a SUPER_ADMIN creates a patient");
        }
        userRepository.findById(request.getAshaWorkerId())
                .orElseThrow(() -> new ResourceNotFoundException("User", request.getAshaWorkerId()));
        return request.getAshaWorkerId();
    }

    private void assertOwnership(Patient patient, UserPrincipal principal) {
        if (isAsha(principal) && !patient.getAshaWorkerId().equals(principal.getId())) {
            throw new ForbiddenException("Access denied: this patient belongs to a different ASHA worker");
        }
    }

    private boolean isAsha(UserPrincipal principal) {
        return Role.ASHA.name().equals(principal.getRole());
    }

    private String generatePatientCode() {
        String year   = String.valueOf(Year.now().getValue());
        String prefix = "PT-" + year + "-%";
        Integer lastSeq = patientRepository.findMaxSequenceByYearPrefix(prefix);
        int next = (lastSeq != null ? lastSeq : 0) + 1;
        return "PT-" + year + "-" + String.format("%06d", next);
    }

    private Patient findOrThrow(UUID id) {
        return patientRepository.findById(id)
                .orElseThrow(() -> new PatientNotFoundException(id));
    }
}
