package com.exobios.backend.audit.service;

import com.exobios.backend.audit.dto.AuditLogDto;
import com.exobios.backend.audit.entity.AuditLog;
import com.exobios.backend.audit.entity.enums.AuditAction;
import com.exobios.backend.audit.repository.AuditLogRepository;
import com.exobios.backend.common.dto.PageResponse;
import com.exobios.backend.common.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AuditLogService {

    private final AuditLogRepository auditLogRepository;

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void log(UUID userId,
                    String username,
                    String role,
                    AuditAction action,
                    String entityType,
                    String entityId,
                    String newValue,
                    String ipAddress,
                    String userAgent) {
        AuditLog entry = new AuditLog();
        entry.setUserId(userId);
        entry.setUsername(username);
        entry.setRole(role);
        entry.setAction(action);
        entry.setEntityType(entityType);
        entry.setEntityId(entityId);
        entry.setNewValue(newValue);
        entry.setIpAddress(ipAddress);
        entry.setUserAgent(userAgent);
        auditLogRepository.save(entry);
    }

    @Transactional(readOnly = true)
    public PageResponse<AuditLogDto> findLogs(UUID userId,
                                               String entityType,
                                               AuditAction action,
                                               Instant fromDate,
                                               Instant toDate,
                                               Pageable pageable) {
        Page<AuditLog> page = auditLogRepository.findWithFilters(
                userId, entityType, action, fromDate, toDate, pageable);
        return PageResponse.of(page.map(this::toDto));
    }

    @Transactional(readOnly = true)
    public AuditLogDto findById(UUID id) {
        AuditLog log = auditLogRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Audit log not found: " + id));
        return toDto(log);
    }

    private AuditLogDto toDto(AuditLog log) {
        return AuditLogDto.builder()
                .id(log.getId())
                .userId(log.getUserId())
                .username(log.getUsername())
                .role(log.getRole())
                .action(log.getAction())
                .entityType(log.getEntityType())
                .entityId(log.getEntityId())
                .oldValue(log.getOldValue())
                .newValue(log.getNewValue())
                .ipAddress(log.getIpAddress())
                .userAgent(log.getUserAgent())
                .createdAt(log.getCreatedAt())
                .build();
    }
}
