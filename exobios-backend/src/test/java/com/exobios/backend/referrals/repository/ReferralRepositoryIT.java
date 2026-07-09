package com.exobios.backend.referrals.repository;

import com.exobios.backend.assessments.entity.Assessment;
import com.exobios.backend.assessments.entity.enums.AssessmentStatus;
import com.exobios.backend.assessments.entity.enums.ComplaintCategory;
import com.exobios.backend.assessments.repository.AssessmentRepository;
import com.exobios.backend.patients.entity.Patient;
import com.exobios.backend.patients.entity.enums.Gender;
import com.exobios.backend.patients.entity.enums.PatientStatus;
import com.exobios.backend.patients.repository.PatientRepository;
import com.exobios.backend.referrals.entity.Referral;
import com.exobios.backend.referrals.entity.enums.ReferralPriority;
import com.exobios.backend.referrals.entity.enums.ReferralStatus;
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
import java.util.List;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * referrals.assessment_id carries a real FK to assessments(id), so every referral needs a
 * real persisted Assessment (which itself needs a real Patient + ASHA User). By contrast
 * referrals.patient_id / referrals.asha_worker_id have NO FK constraint in the schema, so
 * those may safely be arbitrary UUIDs that don't necessarily match the assessment's owner —
 * mirroring how the service layer actually populates them (copied from the assessment).
 */
class ReferralRepositoryIT extends AbstractRepositoryIT {

    @Autowired
    private ReferralRepository referralRepository;

    @Autowired
    private AssessmentRepository assessmentRepository;

    @Autowired
    private PatientRepository patientRepository;

    @Autowired
    private UserRepository userRepository;

    private final AtomicInteger seq = new AtomicInteger(0);

    private UUID newAshaWorker() {
        User user = new User();
        user.setPhone("92000" + String.format("%05d", seq.incrementAndGet()));
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

    private UUID newAssessment(UUID patientId, UUID ashaWorkerId) {
        Assessment a = new Assessment();
        a.setAssessmentNumber("AS-2026-" + String.format("%06d", seq.incrementAndGet()));
        a.setPatientId(patientId);
        a.setAshaWorkerId(ashaWorkerId);
        a.setPatientComplaint("Fever and body ache");
        a.setComplaintCategory(ComplaintCategory.FEVER);
        a.setStatus(AssessmentStatus.SUBMITTED);
        a.setAssessedAt(Instant.now());
        return assessmentRepository.saveAndFlush(a).getId();
    }

    private Referral newReferral(UUID assessmentId, UUID patientId, UUID ashaWorkerId) {
        Referral r = new Referral();
        r.setAssessmentId(assessmentId);
        r.setPatientId(patientId);
        r.setAshaWorkerId(ashaWorkerId);
        r.setReferralHospital("District Hospital");
        r.setReferralReason("High-risk pregnancy — needs specialist review");
        r.setPriority(ReferralPriority.HIGH);
        r.setStatus(ReferralStatus.PENDING);
        return r;
    }

    @Test
    void save_persistsAllFieldsAndPopulatesAuditingColumns() {
        UUID ashaId = newAshaWorker();
        UUID patientId = newPatient(ashaId);
        UUID assessmentId = newAssessment(patientId, ashaId);

        Referral saved = referralRepository.saveAndFlush(newReferral(assessmentId, patientId, ashaId));

        assertThat(saved.getId()).isNotNull();
        assertThat(saved.getCreatedAt()).isNotNull();
        assertThat(saved.getStatus()).isEqualTo(ReferralStatus.PENDING);
        assertThat(saved.getPriority()).isEqualTo(ReferralPriority.HIGH);
    }

    @Test
    void save_withUnknownAssessment_violatesForeignKeyConstraint() {
        UUID ashaId = newAshaWorker();
        UUID patientId = newPatient(ashaId);
        Referral orphan = newReferral(UUID.randomUUID(), patientId, ashaId);

        assertThatThrownBy(() -> referralRepository.saveAndFlush(orphan))
                .isInstanceOf(org.springframework.dao.DataIntegrityViolationException.class);
    }

    @Test
    void findAllByAssessmentIdOrderByCreatedAtDesc_returnsNewestFirst() throws InterruptedException {
        UUID ashaId = newAshaWorker();
        UUID patientId = newPatient(ashaId);
        UUID assessmentId = newAssessment(patientId, ashaId);

        Referral first = referralRepository.saveAndFlush(newReferral(assessmentId, patientId, ashaId));
        Thread.sleep(5);
        Referral second = referralRepository.saveAndFlush(newReferral(assessmentId, patientId, ashaId));

        List<Referral> results = referralRepository.findAllByAssessmentIdOrderByCreatedAtDesc(assessmentId);

        assertThat(results).hasSize(2);
        assertThat(results.get(0).getId()).isEqualTo(second.getId());
        assertThat(results.get(1).getId()).isEqualTo(first.getId());
    }

    @Test
    void findAllByPatientIdAndAshaWorkerId_scopesToOwner() {
        UUID ashaA = newAshaWorker();
        UUID ashaB = newAshaWorker();
        UUID patientId = newPatient(ashaA);
        UUID assessmentId = newAssessment(patientId, ashaA);
        referralRepository.saveAndFlush(newReferral(assessmentId, patientId, ashaA));

        Page<Referral> ownerScoped = referralRepository
                .findAllByPatientIdAndAshaWorkerId(patientId, ashaA, PageRequest.of(0, 20));
        Page<Referral> wrongOwner = referralRepository
                .findAllByPatientIdAndAshaWorkerId(patientId, ashaB, PageRequest.of(0, 20));

        assertThat(ownerScoped.getTotalElements()).isEqualTo(1);
        assertThat(wrongOwner.getTotalElements()).isZero();
    }

    @Test
    void findAllByAshaWorkerIdAndStatus_filtersByStatus() {
        UUID ashaId = newAshaWorker();
        UUID patientId = newPatient(ashaId);
        UUID assessmentId = newAssessment(patientId, ashaId);

        Referral pending = newReferral(assessmentId, patientId, ashaId);
        referralRepository.saveAndFlush(pending);

        Referral completed = newReferral(assessmentId, patientId, ashaId);
        completed.setStatus(ReferralStatus.COMPLETED);
        referralRepository.saveAndFlush(completed);

        Page<Referral> pendingOnly = referralRepository
                .findAllByAshaWorkerIdAndStatus(ashaId, ReferralStatus.PENDING, PageRequest.of(0, 20));

        assertThat(pendingOnly.getTotalElements()).isEqualTo(1);
        assertThat(pendingOnly.getContent().get(0).getStatus()).isEqualTo(ReferralStatus.PENDING);
    }

    @Test
    void findAllByStatus_searchesAcrossAllAshaWorkers() {
        UUID ashaA = newAshaWorker();
        UUID ashaB = newAshaWorker();
        UUID patientA = newPatient(ashaA);
        UUID patientB = newPatient(ashaB);
        UUID assessmentA = newAssessment(patientA, ashaA);
        UUID assessmentB = newAssessment(patientB, ashaB);

        referralRepository.saveAndFlush(newReferral(assessmentA, patientA, ashaA));
        referralRepository.saveAndFlush(newReferral(assessmentB, patientB, ashaB));

        Page<Referral> allPending = referralRepository.findAllByStatus(ReferralStatus.PENDING, PageRequest.of(0, 20));

        assertThat(allPending.getTotalElements()).isEqualTo(2);
    }
}
