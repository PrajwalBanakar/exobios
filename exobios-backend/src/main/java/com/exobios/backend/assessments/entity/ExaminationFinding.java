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
@Table(name = "examination_findings")
@Getter
@Setter
@NoArgsConstructor
public class ExaminationFinding {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", updatable = false, nullable = false)
    private UUID id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "assessment_id", nullable = false, unique = true)
    private Assessment assessment;

    @Column(name = "general_appearance", columnDefinition = "TEXT")
    private String generalAppearance;

    @Column(name = "consciousness", length = 100)
    private String consciousness;

    @Column(name = "edema", columnDefinition = "TEXT")
    private String edema;

    @Column(name = "skin", columnDefinition = "TEXT")
    private String skin;

    @Column(name = "respiratory", columnDefinition = "TEXT")
    private String respiratory;

    @Column(name = "cardiovascular", columnDefinition = "TEXT")
    private String cardiovascular;

    @Column(name = "abdominal", columnDefinition = "TEXT")
    private String abdominal;

    @Column(name = "neurological", columnDefinition = "TEXT")
    private String neurological;
}
