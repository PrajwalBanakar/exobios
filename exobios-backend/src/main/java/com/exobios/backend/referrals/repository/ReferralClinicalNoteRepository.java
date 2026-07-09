package com.exobios.backend.referrals.repository;

import com.exobios.backend.referrals.entity.ReferralClinicalNote;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ReferralClinicalNoteRepository extends JpaRepository<ReferralClinicalNote, UUID> {

    List<ReferralClinicalNote> findAllByReferralIdOrderByCreatedAtDesc(UUID referralId);
}
