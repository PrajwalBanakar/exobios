package com.exobios.backend.audit.aspect;

import com.exobios.backend.audit.annotation.Auditable;
import com.exobios.backend.audit.service.AuditLogService;
import com.exobios.backend.security.UserPrincipal;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.annotation.AfterReturning;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import java.lang.reflect.Method;
import java.util.UUID;

@Aspect
@Component
@RequiredArgsConstructor
@Slf4j
public class AuditAspect {

    private final AuditLogService auditLogService;
    private final ObjectMapper objectMapper;

    @AfterReturning(pointcut = "@annotation(auditable)", returning = "returnValue")
    public void afterReturning(JoinPoint joinPoint, Auditable auditable, Object returnValue) {
        try {
            UserPrincipal principal = resolvePrincipal();
            UUID userId   = principal != null ? principal.getId()       : null;
            String username = principal != null ? principal.getUsername() : null;
            String role     = principal != null ? principal.getRole()     : null;

            String entityId = resolveEntityId(auditable, returnValue, joinPoint.getArgs());
            String newValue = serializeToJson(returnValue);
            String ip       = resolveIpAddress();
            String ua       = resolveUserAgent();

            auditLogService.log(
                    userId,
                    username,
                    role,
                    auditable.action(),
                    auditable.entityType(),
                    entityId,
                    newValue,
                    ip,
                    ua
            );
        } catch (Exception ex) {
            log.warn("Audit logging failed for {}.{}: {}",
                    joinPoint.getSignature().getDeclaringTypeName(),
                    joinPoint.getSignature().getName(),
                    ex.getMessage());
        }
    }

    private UserPrincipal resolvePrincipal() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth != null && auth.getPrincipal() instanceof UserPrincipal up) {
            return up;
        }
        return null;
    }

    private String resolveEntityId(Auditable auditable, Object returnValue, Object[] args) {
        if (auditable.entityIdArgIndex() >= 0 && args != null && auditable.entityIdArgIndex() < args.length) {
            Object arg = args[auditable.entityIdArgIndex()];
            return arg != null ? arg.toString() : null;
        }
        if (returnValue == null) {
            return null;
        }
        try {
            Method getId = returnValue.getClass().getMethod("getId");
            Object id = getId.invoke(returnValue);
            return id != null ? id.toString() : null;
        } catch (Exception ignored) {
            return null;
        }
    }

    private String serializeToJson(Object value) {
        if (value == null) {
            return null;
        }
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException ex) {
            return value.toString();
        }
    }

    private String resolveIpAddress() {
        try {
            ServletRequestAttributes attrs =
                    (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
            if (attrs == null) {
                return null;
            }
            String forwarded = attrs.getRequest().getHeader("X-Forwarded-For");
            if (forwarded != null && !forwarded.isBlank()) {
                return forwarded.split(",")[0].trim();
            }
            return attrs.getRequest().getRemoteAddr();
        } catch (Exception ignored) {
            return null;
        }
    }

    private String resolveUserAgent() {
        try {
            ServletRequestAttributes attrs =
                    (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
            if (attrs == null) {
                return null;
            }
            String ua = attrs.getRequest().getHeader("User-Agent");
            return ua != null && ua.length() > 500 ? ua.substring(0, 500) : ua;
        } catch (Exception ignored) {
            return null;
        }
    }
}
