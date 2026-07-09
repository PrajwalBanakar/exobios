package com.exobios.backend.assessments.repository;

import com.exobios.backend.assessments.entity.Assessment;
import com.exobios.backend.assessments.entity.enums.AssessmentStatus;
import com.exobios.backend.assessments.entity.enums.ComplaintCategory;
import com.exobios.backend.patients.entity.Patient;
import com.exobios.backend.patients.entity.enums.Gender;
import com.exobios.backend.patients.entity.enums.PatientStatus;
import com.exobios.backend.patients.repository.PatientRepository;
import com.exobios.backend.testsupport.AbstractRepositoryIT;
import com.exobios.backend.users.entity.User;
import com.exobios.backend.users.entity.enums.Role;
import com.exobios.backend.users.entity.enums.UserStatus;
import com.exobios.backend.users.repository.UserRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;

import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * assessments.patient_id and assessments.asha_worker_id both carry real FK constraints
 * (to patients(id) and users(id) respectively), so every test needs real persisted rows
 * for both, unlike measures/referrals whose patient_id/asha_worker_id columns are unconstrained.
 */
class AssessmentRepositoryIT extends AbstractRepositoryIT {

    @Autowired
    private AssessmentRepository assessmentRepository;

    @Autowired
    private PatientRepository patientRepository;

    @Autowired
    private UserRepository userRepository;

    private final AtomicInteger seq = new AtomicInteger(0);

    private UUID newAshaWorker() {
        User user = new User();
        user.setPhone("91000" + String.format("%05d", seq.incrementAndGet()));
        user.setName("ASHA Worker");
        user.setPasswordHash("hash");
        user.setRole(Role.ASHA);
        user.setStatus(UserStatus.ACTIVE);
        return userRepository.saveAndFlush(user).getId();
    }

    private UUID newPatient(UUID ashaWorkerId) {
        Patient p = new Patient();
        p.setPatientCode("PT-2026-" + String.format("%06d", seq.incrementAndGet()));
        p.setName("Test Patient");
        p.setAge((short) 30);
        p.setGender(Gender.FEMALE);
        p.setDob(LocalDate.of(1996, 1, 1));
        p.setPhone("9876500000");
        p.setVillage("Village");
        p.setDistrict("District");
        p.setState("State");
        p.setAshaWorkerId(ashaWorkerId);
        p.setStatus(PatientStatus.ACTIVE);
        return patientRepository.saveAndFlush(p).getId();
    }

    private Assessment newAssessment(UUID patientId, UUID ashaWorkerId) {
        Assessment a = new Assessment();
        a.setAssessmentNumber("AS-2026-" + String.format("%06d", seq.incrementAndGet()));
        a.setPatientId(patientId);
        a.setAshaWorkerId(ashaWorkerId);
        a.setPatientComplaint("Fever and body ache");
        a.setComplaintCategory(ComplaintCategory.FEVER);
        a.setStatus(AssessmentStatus.DRAFT);
        a.setAssessedAt(Instant.now());
        return a;
    }

    @Test
    void save_persistsAllFieldsAndPopulatesAuditingColumns() {
        UUID ashaId = newAshaWorker();
        UUID patientId = newPatient(ashaId);

        Assessment saved = assessmentRepository.saveAndFlush(newAssessment(patientId, ashaId));

        assertThat(saved.getId()).isNotNull();
        assertThat(saved.getCreatedAt()).isNotNull();
        assertThat(saved.getStatus()).isEqualTo(AssessmentStatus.DRAFT);

        Assessment reloaded = assessmentRepository.findById(saved.getId()).orElseThrow();
        assertThat(reloaded.getPatientId()).isEqualTo(patientId);
        assertThat(reloaded.getAshaWorkerId()).isEqualTo(ashaId);
    }

    @Test
    void save_withUnknownPatient_violatesForeignKeyConstraint() {
        UUID ashaId = newAshaWorker();
        Assessment orphan = newAssessment(UUID.randomUUID(), ashaId);

        org.assertj.core.api.Assertions.assertThatThrownBy(() -> assessmentRepository.saveAndFlush(orphan))
                .isInstanceOf(org.springframework.dao.DataIntegrityViolationException.class);
    }

    @Test
    void findAllByPatientId_returnsOnlyThatPatientsAssessments() {
        UUID ashaId = newAshaWorker();
        UUID patientA = newPatient(ashaId);
        UUID patientB = newPatient(ashaId);
        assessmentRepository.saveAndFlush(newAssessment(patientA, ashaId));
        assessmentRepository.saveAndFlush(newAssessment(patientA, ashaId));
        assessmentRepository.saveAndFlush(newAssessment(patientB, ashaId));

        Page<Assessment> page = assessmentRepository.findAllByPatientId(patientA, PageRequest.of(0, 20));

        assertThat(page.getTotalElements()).isEqualTo(2);
    }

    @Test
    void findAllByPatientIdAndAshaWorkerId_scopesToBothPatientAndOwner() {
        UUID ashaA = newAshaWorker();
        UUID ashaB = newAshaWorker();
        UUID patient = newPatient(ashaA);
        assessmentRepository.saveAndFlush(newAssessment(patient, ashaA));

        Page<Assessment> matchesOwner = assessmentRepository
                .findAllByPatientIdAndAshaWorkerId(patient, ashaA, PageRequest.of(0, 20));
        Page<Assessment> wrongOwner = assessmentRepository
                .findAllByPatientIdAndAshaWorkerId(patient, ashaB, PageRequest.of(0, 20));

        assertThat(matchesOwner.getTotalElements()).isEqualTo(1);
        assertThat(wrongOwner.getTotalElements()).isZero();
    }

    @Test
    void findMaxSequenceByYearPrefix_returnsHighestExistingSequenceNumber() {
        UUID ashaId = newAshaWorker();
        UUID patientId = newPatient(ashaId);
        Assessment a1 = newAssessment(patientId, ashaId);
        a1.setAssessmentNumber("AS-2027-000004");
        Assessment a2 = newAssessment(patientId, ashaId);
        a2.setAssessmentNumber("AS-2027-000011");
        assessmentRepository.saveAndFlush(a1);
        assessmentRepository.saveAndFlush(a2);

        Integer max = assessmentRepository.findMaxSequenceByYearPrefix("AS-2027-%");

        assertThat(max).isEqualTo(11);
    }
}
