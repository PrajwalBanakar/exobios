-- ─────────────────────────────────────────────────────────────────────────────
-- V7 — Field Operations: sos_records, notifications, feedback, devices
-- ─────────────────────────────────────────────────────────────────────────────

-- SOS / Emergency records
CREATE TABLE sos_records (
    id               UUID         NOT NULL DEFAULT gen_random_uuid(),
    patient_id       UUID         NOT NULL,
    assessment_id    UUID,
    asha_worker_id   UUID         NOT NULL,
    type             VARCHAR(30)  NOT NULL,
    description      TEXT,
    latitude         DECIMAL(10,7),
    longitude        DECIMAL(10,7),
    status           VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE',
    resolved_at      TIMESTAMP WITH TIME ZONE,
    created_by       VARCHAR(100),
    updated_by       VARCHAR(100),
    created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_sos_records PRIMARY KEY (id)
);

CREATE INDEX idx_sos_records_asha_worker_id ON sos_records (asha_worker_id);
CREATE INDEX idx_sos_records_patient_id     ON sos_records (patient_id);
CREATE INDEX idx_sos_records_status         ON sos_records (status);

-- Notifications
CREATE TABLE notifications (
    id               UUID         NOT NULL DEFAULT gen_random_uuid(),
    user_id          UUID         NOT NULL,
    type             VARCHAR(50)  NOT NULL,
    title            VARCHAR(200) NOT NULL,
    message          TEXT         NOT NULL,
    reference_type   VARCHAR(50),
    reference_id     UUID,
    is_read          BOOLEAN      NOT NULL DEFAULT FALSE,
    read_at          TIMESTAMP WITH TIME ZONE,
    created_by       VARCHAR(100),
    updated_by       VARCHAR(100),
    created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_notifications PRIMARY KEY (id)
);

CREATE INDEX idx_notifications_user_id ON notifications (user_id);
CREATE INDEX idx_notifications_unread  ON notifications (user_id, is_read);

-- Feedback
CREATE TABLE feedback (
    id               UUID         NOT NULL DEFAULT gen_random_uuid(),
    submitted_by     UUID         NOT NULL,
    category         VARCHAR(30)  NOT NULL,
    rating           SMALLINT     CHECK (rating BETWEEN 1 AND 5),
    comment          TEXT         NOT NULL,
    response         TEXT,
    responded_by     UUID,
    responded_at     TIMESTAMP WITH TIME ZONE,
    status           VARCHAR(20)  NOT NULL DEFAULT 'OPEN',
    created_by       VARCHAR(100),
    updated_by       VARCHAR(100),
    created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_feedback PRIMARY KEY (id)
);

CREATE INDEX idx_feedback_submitted_by ON feedback (submitted_by);
CREATE INDEX idx_feedback_status       ON feedback (status);

-- Devices
CREATE TABLE devices (
    id               UUID         NOT NULL DEFAULT gen_random_uuid(),
    device_id        VARCHAR(100) NOT NULL,
    name             VARCHAR(200) NOT NULL,
    type             VARCHAR(30)  NOT NULL,
    model            VARCHAR(100),
    assigned_to      UUID,
    status           VARCHAR(20)  NOT NULL DEFAULT 'AVAILABLE',
    battery_level    SMALLINT     CHECK (battery_level BETWEEN 0 AND 100),
    last_synced_at   TIMESTAMP WITH TIME ZONE,
    created_by       VARCHAR(100),
    updated_by       VARCHAR(100),
    created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_devices      PRIMARY KEY (id),
    CONSTRAINT uq_device_id    UNIQUE (device_id)
);

CREATE INDEX idx_devices_assigned_to ON devices (assigned_to);
CREATE INDEX idx_devices_status      ON devices (status);
