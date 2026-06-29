package com.exobios.backend.common.exception;

import com.exobios.backend.common.enums.ApiErrorCode;
import org.springframework.http.HttpStatus;

public class ForbiddenException extends BusinessException {

    public ForbiddenException(String message) {
        super(ApiErrorCode.FORBIDDEN, message, HttpStatus.FORBIDDEN);
    }
}
