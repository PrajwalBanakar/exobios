-- ─────────────────────────────────────────────────────────────────
-- V5 — Clinical Decision Support
--      Extends AI result; adds Measures and Referrals tables
-- ─────────────────────────────────────────────────────────────────

-- ── Extend AI Assessment Results ──────────────────────────────────
ALTER TABLE ai_assessment_results
    ADD COLUMN IF NOT EXISTS red_flags          TEXT,
    ADD COLUMN IF NOT EXISTS processing_time_ms BIGINT,
    ADD COLUMN IF NOT EXISTS model_version      VARCHAR(50),
    ADD COLUMN IF NOT EXISTS status             VARCHAR(20) NOT NULL DEFAULT 'PENDING';

-- ── Measures ──────────────────────────────────────────────────────
CREATE TABLE measures (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    assessment_id   UUID         NOT NULL REFERENCES assessments(id),
    patient_id      UUID         NOT NULL,
    asha_worker_id  UUID         NOT NULL,
    action          VARCHAR(200) NOT NULL,
    category        VARCHAR(50),
    description     TEXT,
    implemented_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    implemented_by  VARCHAR(200),
    outcome         TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      VARCHAR(100),
    updated_by      VARCHAR(100),
    CONSTRAINT pk_measures PRIMARY KEY (id)
);

CREATE INDEX idx_measures_assessment_id  ON measures (assessment_id);
CREATE INDEX idx_measures_patient_id     ON measures (patient_id);
CREATE INDEX idx_measures_asha_worker_id ON measures (asha_worker_id);

-- ── Referrals ─────────────────────────────────────────────────────
CREATE TABLE referrals (
    id               UUID         NOT NULL DEFAULT gen_random_uuid(),
    assessment_id    UUID         NOT NULL REFERENCES assessments(id),
    patient_id       UUID         NOT NULL,
    asha_worker_id   UUID         NOT NULL,
    referral_hospital VARCHAR(200),
    referral_doctor   VARCHAR(200),
    referral_reason  TEXT         NOT NULL,
    priority         VARCHAR(10)  NOT NULL DEFAULT 'MEDIUM'
        CHECK (priority IN ('LOW','MEDIUM','HIGH','URGENT')),
    status           VARCHAR(20)  NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING','ACCEPTED','COMPLETED','REJECTED','CANCELLED')),
    follow_up_date   DATE,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by       VARCHAR(100),
    updated_by       VARCHAR(100),
    CONSTRAINT pk_referrals PRIMARY KEY (id)
);

CREATE INDEX idx_referrals_assessment_id  ON referrals (assessment_id);
CREATE INDEX idx_referrals_patient_id     ON referrals (patient_id);
CREATE INDEX idx_referrals_asha_worker_id ON referrals (asha_worker_id);
CREATE INDEX idx_referrals_status         ON referrals (status);
