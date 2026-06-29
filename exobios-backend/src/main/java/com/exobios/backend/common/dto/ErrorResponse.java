package com.exobios.backend.common.dto;

import com.exobios.backend.common.enums.ApiErrorCode;
import com.fasterxml.jackson.annotation.JsonInclude;

import java.time.Instant;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class ErrorResponse {

    private final ApiErrorCode code;
    private final String       message;
    private final Object       details;
    private final String       path;
    private final Instant      timestamp;

    private ErrorResponse(ApiErrorCode code, String message, Object details, String path) {
        this.code      = code;
        this.message   = message;
        this.details   = details;
        this.path      = path;
        this.timestamp = Instant.now();
    }

    // ── Factory methods ───────────────────────────────────────────────────────

    public static ErrorResponse of(ApiErrorCode code, String message, String path) {
        return new ErrorResponse(code, message, null, path);
    }

    public static ErrorResponse of(ApiErrorCode code, String message, Object details, String path) {
        return new ErrorResponse(code, message, details, path);
    }

    // ── Accessors ─────────────────────────────────────────────────────────────

    public ApiErrorCode getCode()      { return code;      }
    public String       getMessage()   { return message;   }
    public Object       getDetails()   { return details;   }
    public String       getPath()      { return path;      }
    public Instant      getTimestamp() { return timestamp; }
}
