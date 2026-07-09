package com.exobios.backend.referrals.entity;

import com.exobios.backend.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.UUID;

@Entity
@Table(name = "referral_clinical_notes")
@Getter
@Setter
@NoArgsConstructor
public class ReferralClinicalNote extends BaseEntity {

    @Column(name = "referral_id", nullable = false)
    private UUID referralId;

    @Column(name = "note", columnDefinition = "TEXT", nullable = false)
    private String note;
}
