package com.exobios.backend.measures.exception;

import com.exobios.backend.common.exception.ResourceNotFoundException;

import java.util.UUID;

public class MeasureNotFoundException extends ResourceNotFoundException {

    public MeasureNotFoundException(UUID id) {
        super("Measure", id);
    }
}
