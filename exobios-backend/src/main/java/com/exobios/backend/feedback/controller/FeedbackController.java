package com.exobios.backend.feedback.controller;

import com.exobios.backend.common.dto.ApiResponse;
import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.feedback.dto.CreateFeedbackRequest;
import com.exobios.backend.feedback.dto.FeedbackDto;
import com.exobios.backend.feedback.dto.RespondFeedbackRequest;
import com.exobios.backend.feedback.entity.enums.FeedbackStatus;
import com.exobios.backend.feedback.service.FeedbackService;
import com.exobios.backend.security.UserPrincipal;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/feedback")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ASHA', 'SUPER_ADMIN')")
@Tag(name = "Feedback", description = "ASHA worker feedback — submit, view, and respond")
public class FeedbackController {

    private final FeedbackService feedbackService;

    @PostMapping
    @Operation(summary = "Submit feedback (ASHA and SUPER_ADMIN)")
    public ResponseEntity<ApiResponse<FeedbackDto>> submitFeedback(
            @Valid @RequestBody CreateFeedbackRequest request,
            @AuthenticationPrincipal UserPrincipal principal) {
        FeedbackDto created = feedbackService.submitFeedback(request, principal);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("Feedback submitted", created));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get feedback by ID")
    public ResponseEntity<ApiResponse<FeedbackDto>> getFeedbackById(
            @PathVariable UUID id,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(feedbackService.getFeedbackById(id, principal)));
    }

    @GetMapping
    @Operation(summary = "List feedback — ASHA: own; ADMIN: all. Optional ?status filter")
    public ResponseEntity<ApiResponse<PageResponse<FeedbackDto>>> listFeedback(
            @RequestParam(required = false) FeedbackStatus status,
            @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC)
            Pageable pageable,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success(
                feedbackService.listFeedback(status, pageable, principal)));
    }

    @PatchMapping("/{id}/respond")
    @Operation(summary = "Respond to feedback (SUPER_ADMIN only)")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public ResponseEntity<ApiResponse<FeedbackDto>> respondToFeedback(
            @PathVariable UUID id,
            @Valid @RequestBody RespondFeedbackRequest request,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success("Response submitted",
                feedbackService.respondToFeedback(id, request, principal)));
    }

    @PatchMapping("/{id}/close")
    @Operation(summary = "Close feedback (SUPER_ADMIN only)")
    @PreAuthorize("hasRole('SUPER_ADMIN')")
    public ResponseEntity<ApiResponse<FeedbackDto>> closeFeedback(
            @PathVariable UUID id,
            @AuthenticationPrincipal UserPrincipal principal) {
        return ResponseEntity.ok(ApiResponse.success("Feedback closed",
                feedbackService.closeFeedback(id, principal)));
    }
}
