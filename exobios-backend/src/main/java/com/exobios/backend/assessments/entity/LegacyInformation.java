package com.exobios.backend.assessments.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.UUID;

@Entity
@Table(name = "legacy_information")
@Getter
@Setter
@NoArgsConstructor
public class LegacyInformation {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", updatable = false, nullable = false)
    private UUID id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "assessment_id", nullable = false, unique = true)
    private Assessment assessment;

    @Column(name = "family_support", columnDefinition = "TEXT")
    private String familySupport;

    @Column(name = "living_conditions", columnDefinition = "TEXT")
    private String livingConditions;

    @Column(name = "previous_interventions", columnDefinition = "TEXT")
    private String previousInterventions;

    @Column(name = "notes", columnDefinition = "TEXT")
    private String notes;
}
