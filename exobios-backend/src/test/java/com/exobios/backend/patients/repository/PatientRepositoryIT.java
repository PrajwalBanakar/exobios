package com.exobios.backend.patients.repository;

import com.exobios.backend.patients.entity.Patient;
import com.exobios.backend.patients.entity.enums.Gender;
import com.exobios.backend.patients.entity.enums.PatientStatus;
import com.exobios.backend.testsupport.AbstractRepositoryIT;
import com.exobios.backend.users.entity.User;
import com.exobios.backend.users.entity.enums.Role;
import com.exobios.backend.users.entity.enums.UserStatus;
import com.exobios.backend.users.repository.UserRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;

import java.time.LocalDate;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * Exercises PatientRepository against a real PostgreSQL container (Testcontainers) with
 * the actual Flyway-migrated schema — entity/column mapping, NOT NULL / UNIQUE / FOREIGN
 * KEY constraints, JPA auditing, and the hand-written JPQL/native queries all run for real.
 */
class PatientRepositoryIT extends AbstractRepositoryIT {

    @Autowired
    private PatientRepository patientRepository;

    @Autowired
    private UserRepository userRepository;

    private final AtomicInteger phoneSeq = new AtomicInteger(0);

    // patients.asha_worker_id carries a real FK to users(id) — every test needs an
    // actual persisted ASHA user to reference, not just a random UUID.
    private User newAshaWorker() {
        User user = new User();
        user.setPhone("90000" + String.format("%05d", phoneSeq.incrementAndGet()));
        user.setName("ASHA Worker");
        user.setPasswordHash("hash");
        user.setRole(Role.ASHA);
        user.setStatus(UserStatus.ACTIVE);
        return userRepository.saveAndFlush(user);
    }

    private Patient newPatient(String code, String name, UUID ashaWorkerId) {
        Patient p = new Patient();
        p.setPatientCode(code);
        p.setName(name);
        p.setAge((short) 28);
        p.setGender(Gender.FEMALE);
        p.setDob(LocalDate.of(1997, 3, 15));
        p.setPhone("9876543210");
        p.setVillage("Rampur Village");
        p.setDistrict("Rampur");
        p.setState("Uttar Pradesh");
        p.setAshaWorkerId(ashaWorkerId);
        p.setStatus(PatientStatus.ACTIVE);
        return p;
    }

    @Test
    void save_persistsAllFieldsAndPopulatesAuditingColumns() {
        UUID ashaWorkerId = newAshaWorker().getId();
        Patient saved = patientRepository.saveAndFlush(newPatient("PT-2026-000001", "Priya Sharma", ashaWorkerId));

        assertThat(saved.getId()).isNotNull();
        assertThat(saved.getCreatedAt()).isNotNull();
        assertThat(saved.getUpdatedAt()).isNotNull();
        assertThat(saved.getStatus()).isEqualTo(PatientStatus.ACTIVE);

        Patient reloaded = patientRepository.findById(saved.getId()).orElseThrow();
        assertThat(reloaded.getName()).isEqualTo("Priya Sharma");
        assertThat(reloaded.getGender()).isEqualTo(Gender.FEMALE);
        assertThat(reloaded.getAshaWorkerId()).isEqualTo(ashaWorkerId);
    }

    @Test
    void save_withoutAKnownAshaWorker_violatesForeignKeyConstraint() {
        Patient orphan = newPatient("PT-2026-999999", "Ghost Patient", UUID.randomUUID());

        assertThatThrownBy(() -> patientRepository.saveAndFlush(orphan))
                .isInstanceOf(DataIntegrityViolationException.class);
    }

    @Test
    void save_withDuplicatePatientCode_violatesUniqueConstraint() {
        UUID ashaWorkerId = newAshaWorker().getId();
        patientRepository.saveAndFlush(newPatient("PT-2026-000002", "Priya Sharma", ashaWorkerId));

        Patient duplicate = newPatient("PT-2026-000002", "Another Patient", ashaWorkerId);
        assertThatThrownBy(() -> patientRepository.saveAndFlush(duplicate))
                .isInstanceOf(DataIntegrityViolationException.class);
    }

    @Test
    void findAllByAshaWorkerId_returnsOnlyThatAshasPatients() {
        UUID ashaA = newAshaWorker().getId();
        UUID ashaB = newAshaWorker().getId();
        patientRepository.saveAndFlush(newPatient("PT-2026-100001", "Patient A1", ashaA));
        patientRepository.saveAndFlush(newPatient("PT-2026-100002", "Patient A2", ashaA));
        patientRepository.saveAndFlush(newPatient("PT-2026-100003", "Patient B1", ashaB));

        Page<Patient> page = patientRepository.findAllByAshaWorkerId(ashaA, PageRequest.of(0, 20));

        assertThat(page.getTotalElements()).isEqualTo(2);
        assertThat(page.getContent()).extracting(Patient::getName).containsExactlyInAnyOrder("Patient A1", "Patient A2");
    }

    @Test
    void searchByAshaWorkerAndText_matchesNameCaseInsensitively() {
        UUID ashaId = newAshaWorker().getId();
        patientRepository.saveAndFlush(newPatient("PT-2026-200001", "Priya Sharma", ashaId));
        patientRepository.saveAndFlush(newPatient("PT-2026-200002", "Rajesh Kumar", ashaId));

        Page<Patient> results = patientRepository.searchByAshaWorkerAndText(ashaId, "PRIYA", PageRequest.of(0, 20));

        assertThat(results.getContent()).hasSize(1);
        assertThat(results.getContent().get(0).getName()).isEqualTo("Priya Sharma");
    }

    @Test
    void searchByAshaWorkerAndText_matchesVillageAndDoesNotLeakOtherAshaWorkersPatients() {
        UUID ashaA = newAshaWorker().getId();
        UUID ashaB = newAshaWorker().getId();
        Patient inVillage = newPatient("PT-2026-300001", "Anita Devi", ashaA);
        inVillage.setVillage("Lakhimpur Block");
        patientRepository.saveAndFlush(inVillage);

        Patient sameVillageOtherAsha = newPatient("PT-2026-300002", "Someone Else", ashaB);
        sameVillageOtherAsha.setVillage("Lakhimpur Block");
        patientRepository.saveAndFlush(sameVillageOtherAsha);

        Page<Patient> results = patientRepository.searchByAshaWorkerAndText(ashaA, "lakhimpur", PageRequest.of(0, 20));

        assertThat(results.getContent()).hasSize(1);
        assertThat(results.getContent().get(0).getName()).isEqualTo("Anita Devi");
    }

    @Test
    void searchByText_searchesAcrossAllPatientsRegardlessOfOwner() {
        patientRepository.saveAndFlush(newPatient("PT-2026-400001", "Mohammed Iqbal", newAshaWorker().getId()));
        patientRepository.saveAndFlush(newPatient("PT-2026-400002", "Sunita Verma", newAshaWorker().getId()));

        Page<Patient> results = patientRepository.searchByText("iqbal", PageRequest.of(0, 20));

        assertThat(results.getContent()).hasSize(1);
    }

    @Test
    void findMaxSequenceByYearPrefix_returnsZeroWhenNoPatientsExistForThatYear() {
        Integer max = patientRepository.findMaxSequenceByYearPrefix("PT-2099-%");

        assertThat(max).isZero();
    }

    @Test
    void findMaxSequenceByYearPrefix_returnsHighestExistingSequenceNumber() {
        UUID ashaId = newAshaWorker().getId();
        patientRepository.saveAndFlush(newPatient("PT-2026-000005", "Patient Five", ashaId));
        patientRepository.saveAndFlush(newPatient("PT-2026-000012", "Patient Twelve", ashaId));
        patientRepository.saveAndFlush(newPatient("PT-2026-000003", "Patient Three", ashaId));

        Integer max = patientRepository.findMaxSequenceByYearPrefix("PT-2026-%");

        assertThat(max).isEqualTo(12);
    }
}
