package com.exobios.backend.audit.annotation;

import com.exobios.backend.audit.entity.enums.AuditAction;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Marks a service method for audit logging.
 * The aspect captures the caller's identity and the operation result
 * and persists an immutable AuditLog entry after the method succeeds.
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Auditable {

    AuditAction action();

    String entityType();

    /**
     * Index of the method argument (0-based) that holds the entity UUID.
     * Use this for void-returning methods (e.g. DELETE) where the ID cannot
     * be extracted from the return value.
     * Default -1 means: extract from the return value via getId().
     */
    int entityIdArgIndex() default -1;
}
