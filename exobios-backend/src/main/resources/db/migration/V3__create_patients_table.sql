-- ─────────────────────────────────────────────────────────────────────────────
-- V3 : Create patients table
-- patient_code format: PT-YYYY-000001 (generated at service layer for now;
-- future improvement: replace with a dedicated PostgreSQL sequence per year).
-- aadhaar_number is stored encrypted at rest (column level) in production;
-- responses always return a masked value — never the raw number.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE patients (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    patient_code    VARCHAR(20) NOT NULL UNIQUE,
    name            VARCHAR(100) NOT NULL,
    age             SMALLINT    CHECK (age >= 0 AND age <= 120),
    gender          VARCHAR(10) CHECK (gender IN ('MALE', 'FEMALE', 'OTHER')),
    dob             DATE,
    phone           VARCHAR(20),
    address         TEXT,
    village         VARCHAR(100),
    district        VARCHAR(100),
    state           VARCHAR(100),
    aadhaar_number  VARCHAR(12),
    asha_worker_id  UUID        NOT NULL REFERENCES users(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
                                CHECK (status IN ('ACTIVE', 'INACTIVE', 'DECEASED')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      VARCHAR(100),
    updated_by      VARCHAR(100),

    CONSTRAINT pk_patients PRIMARY KEY (id)
);

CREATE INDEX idx_patients_patient_code   ON patients (patient_code);
CREATE INDEX idx_patients_name           ON patients (name);
CREATE INDEX idx_patients_phone          ON patients (phone) WHERE phone IS NOT NULL;
CREATE INDEX idx_patients_village        ON patients (village) WHERE village IS NOT NULL;
CREATE INDEX idx_patients_asha_worker_id ON patients (asha_worker_id);
CREATE INDEX idx_patients_status         ON patients (status);
