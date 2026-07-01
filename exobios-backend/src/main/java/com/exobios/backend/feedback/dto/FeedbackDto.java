package com.exobios.backend.feedback.dto;

import com.exobios.backend.feedback.entity.enums.FeedbackCategory;
import com.exobios.backend.feedback.entity.enums.FeedbackStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.UUID;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FeedbackDto {
    private UUID             id;
    private UUID             submittedBy;
    private FeedbackCategory category;
    private Integer          rating;
    private String           comment;
    private String           response;
    private UUID             respondedBy;
    private Instant          respondedAt;
    private FeedbackStatus   status;
    private Instant          createdAt;
    private Instant          updatedAt;
}
