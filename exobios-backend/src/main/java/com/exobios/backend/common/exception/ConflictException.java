package com.exobios.backend.common.exception;

import com.exobios.backend.common.enums.ApiErrorCode;
import org.springframework.http.HttpStatus;

public class ConflictException extends BusinessException {

    public ConflictException(String message) {
        super(ApiErrorCode.CONFLICT, message, HttpStatus.CONFLICT);
    }
}
