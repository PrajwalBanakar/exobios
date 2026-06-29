package com.exobios.backend.common.exception;

import com.exobios.backend.common.enums.ApiErrorCode;
import org.springframework.http.HttpStatus;

public class UnauthorizedException extends BusinessException {

    public UnauthorizedException(String message) {
        super(ApiErrorCode.UNAUTHORIZED, message, HttpStatus.UNAUTHORIZED);
    }
}
