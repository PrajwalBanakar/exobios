package com.exobios.backend.common.exception;

import com.exobios.backend.common.dto.ApiResponse;
import com.exobios.backend.common.dto.ErrorResponse;
import com.exobios.backend.common.enums.ApiErrorCode;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolationException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.LinkedHashMap;
import java.util.Map;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ApiResponse<ErrorResponse>> handleBusinessException(
            BusinessException ex, HttpServletRequest request) {
        log.warn("Business exception [{}] on {}: {}", ex.getErrorCode(), request.getRequestURI(), ex.getMessage());
        ErrorResponse error = ErrorResponse.of(ex.getErrorCode(), ex.getMessage(), request.getRequestURI());
        return ResponseEntity.status(ex.getHttpStatus()).body(ApiResponse.error(ex.getMessage(), error));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<ErrorResponse>> handleValidation(
            MethodArgumentNotValidException ex, HttpServletRequest request) {
        Map<String, String> fieldErrors = new LinkedHashMap<>();
        for (FieldError fe : ex.getBindingResult().getFieldErrors()) {
            fieldErrors.put(fe.getField(), fe.getDefaultMessage());
        }
        log.warn("Validation failed on {}: {}", request.getRequestURI(), fieldErrors);
        ErrorResponse error = ErrorResponse.of(
                ApiErrorCode.VALIDATION_ERROR, "Validation failed", fieldErrors, request.getRequestURI());
        return ResponseEntity.badRequest().body(ApiResponse.error("Validation failed", error));
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ApiResponse<ErrorResponse>> handleConstraintViolation(
            ConstraintViolationException ex, HttpServletRequest request) {
        Map<String, String> violations = new LinkedHashMap<>();
        ex.getConstraintViolations()
                .forEach(cv -> violations.put(cv.getPropertyPath().toString(), cv.getMessage()));
        log.warn("Constraint violation on {}: {}", request.getRequestURI(), violations);
        ErrorResponse error = ErrorResponse.of(
                ApiErrorCode.VALIDATION_ERROR, "Constraint violation", violations, request.getRequestURI());
        return ResponseEntity.badRequest().body(ApiResponse.error("Validation failed", error));
    }

    // Catches AuthenticationException thrown inside MVC controllers.
    // Filter-level auth failures (missing/expired JWT) are handled by JwtAuthenticationEntryPoint
    // which will be wired in SecurityConfig (Step 3).
    @ExceptionHandler(AuthenticationException.class)
    public ResponseEntity<ApiResponse<ErrorResponse>> handleAuthentication(
            AuthenticationException ex, HttpServletRequest request) {
        log.warn("Authentication exception on {}: {}", request.getRequestURI(), ex.getMessage());
        ErrorResponse error = ErrorResponse.of(
                ApiErrorCode.UNAUTHORIZED, "Authentication required", request.getRequestURI());
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(ApiResponse.error("Authentication required", error));
    }

    // Catches AccessDeniedException thrown inside MVC controllers and @PreAuthorize checks.
    // Filter-level access denials are handled by JwtAccessDeniedHandler (Step 3).
    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ApiResponse<ErrorResponse>> handleAccessDenied(
            AccessDeniedException ex, HttpServletRequest request) {
        log.warn("Access denied on {}: {}", request.getRequestURI(), ex.getMessage());
        ErrorResponse error = ErrorResponse.of(
                ApiErrorCode.FORBIDDEN, "Access denied", request.getRequestURI());
        return ResponseEntity.status(HttpStatus.FORBIDDEN)
                .body(ApiResponse.error("Access denied", error));
    }

    // Catches unique-constraint violations that slip past pre-checks under concurrent
    // writes (e.g. a generated code/number colliding, or two requests racing a uniqueness
    // pre-check) — maps to a client-correctable 409 instead of an opaque 500.
    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<ApiResponse<ErrorResponse>> handleDataIntegrityViolation(
            DataIntegrityViolationException ex, HttpServletRequest request) {
        log.warn("Data integrity violation on {}: {}", request.getRequestURI(), ex.getMessage());
        ErrorResponse error = ErrorResponse.of(
                ApiErrorCode.CONFLICT, "The request conflicts with existing data", request.getRequestURI());
        return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(ApiResponse.error("Conflict", error));
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiResponse<ErrorResponse>> handleMessageNotReadable(
            HttpMessageNotReadableException ex, HttpServletRequest request) {
        log.warn("Unreadable request body on {}: {}", request.getRequestURI(), ex.getMessage());
        ErrorResponse error = ErrorResponse.of(
                ApiErrorCode.BAD_REQUEST, "Malformed or unreadable request body", request.getRequestURI());
        return ResponseEntity.badRequest().body(ApiResponse.error("Malformed request body", error));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<ErrorResponse>> handleGeneric(
            Exception ex, HttpServletRequest request) {
        log.error("Unhandled exception on {}: {}", request.getRequestURI(), ex.getMessage(), ex);
        ErrorResponse error = ErrorResponse.of(
                ApiErrorCode.INTERNAL_SERVER_ERROR, "An unexpected error occurred", request.getRequestURI());
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.error("Internal server error", error));
    }
}
