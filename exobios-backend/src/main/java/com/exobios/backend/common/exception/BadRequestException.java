package com.exobios.backend.common.exception;

import com.exobios.backend.common.enums.ApiErrorCode;
import org.springframework.http.HttpStatus;

public class BadRequestException extends BusinessException {

    public BadRequestException(String message) {
        super(ApiErrorCode.BAD_REQUEST, message, HttpStatus.BAD_REQUEST);
    }
}
