package com.exobios.backend.feedback.repository;

import com.exobios.backend.feedback.entity.Feedback;
import com.exobios.backend.feedback.entity.enums.FeedbackStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface FeedbackRepository extends JpaRepository<Feedback, UUID> {

    Page<Feedback> findAllBySubmittedBy(UUID submittedBy, Pageable pageable);

    Page<Feedback> findAllBySubmittedByAndStatus(UUID submittedBy, FeedbackStatus status, Pageable pageable);

    Page<Feedback> findAllByStatus(FeedbackStatus status, Pageable pageable);
}
