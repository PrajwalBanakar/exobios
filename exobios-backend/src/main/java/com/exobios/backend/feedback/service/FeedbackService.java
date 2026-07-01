package com.exobios.backend.feedback.service;

import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.common.exception.BadRequestException;
import com.exobios.backend.common.exception.ForbiddenException;
import com.exobios.backend.feedback.dto.CreateFeedbackRequest;
import com.exobios.backend.feedback.dto.FeedbackDto;
import com.exobios.backend.feedback.dto.RespondFeedbackRequest;
import com.exobios.backend.feedback.entity.Feedback;
import com.exobios.backend.feedback.entity.enums.FeedbackStatus;
import com.exobios.backend.feedback.exception.FeedbackNotFoundException;
import com.exobios.backend.feedback.mapper.FeedbackMapper;
import com.exobios.backend.feedback.repository.FeedbackRepository;
import com.exobios.backend.security.UserPrincipal;
import com.exobios.backend.users.entity.enums.Role;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.exobios.backend.audit.annotation.Auditable;
import com.exobios.backend.audit.entity.enums.AuditAction;
import java.time.Instant;
import java.util.UUID;

@Slf4j
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class FeedbackService {

    private final FeedbackRepository feedbackRepository;
    private final FeedbackMapper     feedbackMapper;

    @Auditable(action = AuditAction.CREATE, entityType = "FEEDBACK")
    @Transactional
    public FeedbackDto submitFeedback(CreateFeedbackRequest request, UserPrincipal principal) {
        Feedback feedback = new Feedback();
        feedback.setSubmittedBy(principal.getId());
        feedback.setCategory(request.getCategory());
        feedback.setRating(request.getRating());
        feedback.setComment(request.getComment());
        feedback.setStatus(FeedbackStatus.OPEN);

        Feedback saved = feedbackRepository.save(feedback);
        log.info("Feedback submitted id={} by user={}", saved.getId(), principal.getId());
        return feedbackMapper.toDto(saved);
    }

    public FeedbackDto getFeedbackById(UUID id, UserPrincipal principal) {
        Feedback feedback = findOrThrow(id);
        assertReadAccess(feedback, principal);
        return feedbackMapper.toDto(feedback);
    }

    public PageResponse<FeedbackDto> listFeedback(FeedbackStatus status, Pageable pageable,
                                                   UserPrincipal principal) {
        Page<Feedback> page;
        if (isAsha(principal)) {
            page = status != null
                    ? feedbackRepository.findAllBySubmittedByAndStatus(principal.getId(), status, pageable)
                    : feedbackRepository.findAllBySubmittedBy(principal.getId(), pageable);
        } else {
            page = status != null
                    ? feedbackRepository.findAllByStatus(status, pageable)
                    : feedbackRepository.findAll(pageable);
        }
        return PageResponse.of(page.map(feedbackMapper::toDto));
    }

    @Auditable(action = AuditAction.UPDATE, entityType = "FEEDBACK")
    @Transactional
    public FeedbackDto respondToFeedback(UUID id, RespondFeedbackRequest request,
                                          UserPrincipal principal) {
        Feedback feedback = findOrThrow(id);
        if (feedback.getStatus() == FeedbackStatus.CLOSED) {
            throw new BadRequestException("Cannot respond to CLOSED feedback");
        }
        feedback.setResponse(request.getResponse());
        feedback.setRespondedBy(principal.getId());
        feedback.setRespondedAt(Instant.now());
        feedback.setStatus(FeedbackStatus.RESPONDED);
        log.info("Feedback id={} responded by admin={}", id, principal.getId());
        return feedbackMapper.toDto(feedbackRepository.save(feedback));
    }

    @Auditable(action = AuditAction.STATUS_CHANGE, entityType = "FEEDBACK")
    @Transactional
    public FeedbackDto closeFeedback(UUID id, UserPrincipal principal) {
        Feedback feedback = findOrThrow(id);
        if (feedback.getStatus() == FeedbackStatus.CLOSED) {
            throw new BadRequestException("Feedback is already CLOSED");
        }
        feedback.setStatus(FeedbackStatus.CLOSED);
        log.info("Feedback id={} closed by admin={}", id, principal.getId());
        return feedbackMapper.toDto(feedbackRepository.save(feedback));
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private Feedback findOrThrow(UUID id) {
        return feedbackRepository.findById(id).orElseThrow(() -> new FeedbackNotFoundException(id));
    }

    private void assertReadAccess(Feedback feedback, UserPrincipal principal) {
        if (isAsha(principal) && !feedback.getSubmittedBy().equals(principal.getId())) {
            throw new ForbiddenException("Access denied: this feedback was submitted by another user");
        }
    }

    private boolean isAsha(UserPrincipal principal) {
        return Role.ASHA.name().equals(principal.getRole());
    }
}
