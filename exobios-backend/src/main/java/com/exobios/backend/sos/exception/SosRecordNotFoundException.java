package com.exobios.backend.sos.exception;

import com.exobios.backend.common.exception.ResourceNotFoundException;

import java.util.UUID;

public class SosRecordNotFoundException extends ResourceNotFoundException {

    public SosRecordNotFoundException(UUID id) {
        super("SosRecord", id);
    }
}
