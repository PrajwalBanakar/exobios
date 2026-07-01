package com.exobios.backend.referrals.repository;

import com.exobios.backend.referrals.entity.Referral;
import com.exobios.backend.referrals.entity.enums.ReferralStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ReferralRepository extends JpaRepository<Referral, UUID> {

    List<Referral> findAllByAssessmentIdOrderByCreatedAtDesc(UUID assessmentId);

    Page<Referral> findAllByPatientId(UUID patientId, Pageable pageable);

    Page<Referral> findAllByAshaWorkerId(UUID ashaWorkerId, Pageable pageable);

    Page<Referral> findAllByAshaWorkerIdAndStatus(UUID ashaWorkerId, ReferralStatus status,
                                                   Pageable pageable);

    Page<Referral> findAllByStatus(ReferralStatus status, Pageable pageable);
}
