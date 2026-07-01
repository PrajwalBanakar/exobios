package com.exobios.backend.audit.controller;

import com.exobios.backend.audit.dto.AuditLogDto;
import com.exobios.backend.audit.entity.enums.AuditAction;
import com.exobios.backend.audit.service.AuditLogService;
import com.exobios.backend.common.dto.ApiResponse;
import com.exobios.backend.common.dto.PageResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/audit")
@RequiredArgsConstructor
@PreAuthorize("hasRole('SUPER_ADMIN')")
@Tag(name = "Audit Logs", description = "Immutable audit trail — SUPER_ADMIN read-only")
public class AuditLogController {

    private final AuditLogService auditLogService;

    @GetMapping("/logs")
    @Operation(summary = "Query audit logs with optional filters")
    public ResponseEntity<ApiResponse<PageResponse<AuditLogDto>>> getLogs(
            @RequestParam(required = false) UUID userId,
            @RequestParam(required = false) String entityType,
            @RequestParam(required = false) AuditAction action,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant fromDate,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Instant toDate,
            @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC)
            Pageable pageable) {
        return ResponseEntity.ok(ApiResponse.success(
                auditLogService.findLogs(userId, entityType, action, fromDate, toDate, pageable)));
    }

    @GetMapping("/logs/{id}")
    @Operation(summary = "Get a single audit log entry by ID")
    public ResponseEntity<ApiResponse<AuditLogDto>> getById(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(auditLogService.findById(id)));
    }
}
