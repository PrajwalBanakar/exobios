package com.exobios.backend.feedback.exception;

import com.exobios.backend.common.exception.ResourceNotFoundException;

import java.util.UUID;

public class FeedbackNotFoundException extends ResourceNotFoundException {

    public FeedbackNotFoundException(UUID id) {
        super("Feedback", id);
    }
}
