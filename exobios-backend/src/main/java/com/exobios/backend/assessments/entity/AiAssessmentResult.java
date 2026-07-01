package com.exobios.backend.assessments.entity;

import com.exobios.backend.assessments.entity.enums.AiResultStatus;
import com.exobios.backend.assessments.entity.enums.RiskLevel;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
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

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "ai_assessment_results")
@Getter
@Setter
@NoArgsConstructor
public class AiAssessmentResult {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", updatable = false, nullable = false)
    private UUID id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "assessment_id", nullable = false, unique = true)
    private Assessment assessment;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private AiResultStatus status = AiResultStatus.PENDING;

    @Column(name = "summary", columnDefinition = "TEXT")
    private String summary;

    @Enumerated(EnumType.STRING)
    @Column(name = "risk_level", length = 10)
    private RiskLevel riskLevel;

    @Column(name = "confidence_score", precision = 5, scale = 4)
    private BigDecimal confidenceScore;

    @Column(name = "red_flags", columnDefinition = "TEXT")
    private String redFlags;

    @Column(name = "recommendations", columnDefinition = "TEXT")
    private String recommendations;

    @Column(name = "processing_time_ms")
    private Long processingTimeMs;

    @Column(name = "model_version", length = 50)
    private String modelVersion;

    @Column(name = "generated_at")
    private Instant generatedAt;

    @Column(name = "source", length = 100)
    private String source;
}
