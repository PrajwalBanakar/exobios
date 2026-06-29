package com.exobios.backend.common.exception;

import com.exobios.backend.common.enums.ApiErrorCode;
import org.springframework.http.HttpStatus;

public class BusinessException extends RuntimeException {

    private final ApiErrorCode errorCode;
    private final HttpStatus   httpStatus;

    public BusinessException(ApiErrorCode errorCode, String message, HttpStatus httpStatus) {
        super(message);
        this.errorCode  = errorCode;
        this.httpStatus = httpStatus;
    }

    public BusinessException(ApiErrorCode errorCode, String message, HttpStatus httpStatus, Throwable cause) {
        super(message, cause);
        this.errorCode  = errorCode;
        this.httpStatus = httpStatus;
    }

    public ApiErrorCode getErrorCode()  { return errorCode;  }
    public HttpStatus   getHttpStatus() { return httpStatus; }
}
