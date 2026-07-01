-- ─────────────────────────────────────────────────────────────────────────────
-- V8 — Audit Logs: immutable record of all write operations
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE audit_logs (
    id           UUID         NOT NULL DEFAULT gen_random_uuid(),
    user_id      UUID,
    username     VARCHAR(100),
    role         VARCHAR(30),
    action       VARCHAR(30)  NOT NULL,
    entity_type  VARCHAR(50),
    entity_id    VARCHAR(36),
    old_value    TEXT,
    new_value    TEXT,
    ip_address   VARCHAR(50),
    user_agent   VARCHAR(500),
    created_at   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_audit_logs PRIMARY KEY (id)
);

CREATE INDEX idx_audit_logs_user_id     ON audit_logs (user_id);
CREATE INDEX idx_audit_logs_entity_type ON audit_logs (entity_type);
CREATE INDEX idx_audit_logs_action      ON audit_logs (action);
CREATE INDEX idx_audit_logs_created_at  ON audit_logs (created_at DESC);
