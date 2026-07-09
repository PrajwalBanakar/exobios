-- ─────────────────────────────────────────────────────────────────────────────
-- V10 : Add DOCTOR role + referral doctor-review lifecycle
--
--   1. Widen users.role CHECK constraint to allow 'DOCTOR'.
--   2. Seed one dev doctor user (password hashed with BCrypt cost 12).
--        DOCTOR : Doctor@123
--   3. Add the doctor-review lifecycle columns to referrals — separate from the
--      existing `status` column, which tracks the destination hospital's
--      outcome (accepted/treated/rejected) and is untouched by this migration.
--   4. New referral_clinical_notes table for doctor comments on a referral.
-- ─────────────────────────────────────────────────────────────────────────────

-- ── 1. Widen role CHECK constraint ─────────────────────────────────
ALTER TABLE users DROP CONSTRAINT users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('ASHA', 'SUPER_ADMIN', 'DOCTOR'));

-- ── 2. Seed dev doctor user ─────────────────────────────────────────
INSERT INTO users (phone, name, password_hash, role, status, created_by, updated_by)
VALUES ('9876500002', 'Demo Doctor',
        '$2a$12$0gC06YLfbRzPShFHQxsN.ey7iKZfAQJq7OOt3u0y3UiKFxXQzWpxS',
        'DOCTOR', 'ACTIVE', 'SYSTEM', 'SYSTEM')
ON CONFLICT (phone) DO NOTHING;

-- ── 3. Referral doctor-review lifecycle columns ─────────────────────
-- NOT NULL DEFAULT backfills every existing row to CREATED automatically.
ALTER TABLE referrals
    ADD COLUMN review_stage VARCHAR(30) NOT NULL DEFAULT 'CREATED'
        CHECK (review_stage IN ('CREATED','ASSIGNED_TO_DOCTOR','UNDER_REVIEW','ACTION_TAKEN','CLOSED')),
    ADD COLUMN assigned_doctor_id UUID,
    ADD COLUMN doctor_recommendation TEXT;

CREATE INDEX idx_referrals_review_stage       ON referrals (review_stage);
CREATE INDEX idx_referrals_assigned_doctor_id ON referrals (assigned_doctor_id);

-- ── 4. Referral clinical notes ───────────────────────────────────────
CREATE TABLE referral_clinical_notes (
    id           UUID        NOT NULL DEFAULT gen_random_uuid(),
    referral_id  UUID        NOT NULL,
    note         TEXT        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by   VARCHAR(100),
    updated_by   VARCHAR(100),
    CONSTRAINT pk_referral_clinical_notes PRIMARY KEY (id)
);

CREATE INDEX idx_referral_clinical_notes_referral_id ON referral_clinical_notes (referral_id);
