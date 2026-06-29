-- ─────────────────────────────────────────────────────────────────────────────
-- V1 : Create users table
-- gen_random_uuid() is built-in from PostgreSQL 13+; no extension required.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE users (
    id            UUID         NOT NULL DEFAULT gen_random_uuid(),
    asha_id       VARCHAR(50)  UNIQUE,
    phone         VARCHAR(20)  NOT NULL UNIQUE,
    name          VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL CHECK (role IN ('ASHA', 'SUPER_ADMIN')),
    area          VARCHAR(100),
    district      VARCHAR(100),
    state         VARCHAR(100),
    status        VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE'
                               CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')),
    last_login_at TIMESTAMPTZ,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by    VARCHAR(100),
    updated_by    VARCHAR(100),

    CONSTRAINT pk_users PRIMARY KEY (id)
);

CREATE INDEX idx_users_phone   ON users (phone);
CREATE INDEX idx_users_asha_id ON users (asha_id) WHERE asha_id IS NOT NULL;
CREATE INDEX idx_users_role    ON users (role);
CREATE INDEX idx_users_status  ON users (status);
