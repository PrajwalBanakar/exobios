package com.exobios.backend.patients.exception;

import com.exobios.backend.common.exception.ResourceNotFoundException;

import java.util.UUID;

public class PatientNotFoundException extends ResourceNotFoundException {

    public PatientNotFoundException(UUID id) {
        super("Patient", id);
    }
}
