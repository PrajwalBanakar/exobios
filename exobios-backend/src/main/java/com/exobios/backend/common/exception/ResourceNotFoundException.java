package com.exobios.backend.common.exception;

import com.exobios.backend.common.enums.ApiErrorCode;
import org.springframework.http.HttpStatus;

public class ResourceNotFoundException extends BusinessException {

    public ResourceNotFoundException(String message) {
        super(ApiErrorCode.RESOURCE_NOT_FOUND, message, HttpStatus.NOT_FOUND);
    }

    public ResourceNotFoundException(String resource, Object id) {
        super(ApiErrorCode.RESOURCE_NOT_FOUND, resource + " not found with id: " + id, HttpStatus.NOT_FOUND);
    }
}
