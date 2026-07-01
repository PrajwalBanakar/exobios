package com.exobios.backend.feedback.entity;

import com.exobios.backend.common.entity.BaseEntity;
import com.exobios.backend.feedback.entity.enums.FeedbackCategory;
import com.exobios.backend.feedback.entity.enums.FeedbackStatus;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "feedback")
@Getter
@Setter
@NoArgsConstructor
public class Feedback extends BaseEntity {

    @Column(name = "submitted_by", nullable = false)
    private UUID submittedBy;

    @Enumerated(EnumType.STRING)
    @Column(name = "category", nullable = false, length = 30)
    private FeedbackCategory category;

    @Column(name = "rating")
    private Integer rating;

    @Column(name = "comment", nullable = false, columnDefinition = "TEXT")
    private String comment;

    @Column(name = "response", columnDefinition = "TEXT")
    private String response;

    @Column(name = "responded_by")
    private UUID respondedBy;

    @Column(name = "responded_at")
    private Instant respondedAt;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private FeedbackStatus status = FeedbackStatus.OPEN;
}
