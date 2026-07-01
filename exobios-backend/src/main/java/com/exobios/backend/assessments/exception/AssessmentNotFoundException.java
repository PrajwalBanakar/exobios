package com.exobios.backend.assessments.exception;

import com.exobios.backend.common.exception.ResourceNotFoundException;

import java.util.UUID;

public class AssessmentNotFoundException extends ResourceNotFoundException {

    public AssessmentNotFoundException(UUID id) {
        super("Assessment", id);
    }
}
