-- ─────────────────────────────────────────────────────────────────
-- V4 — Clinical Assessment tables
-- ─────────────────────────────────────────────────────────────────

CREATE TABLE assessments (
    id                 UUID         NOT NULL DEFAULT gen_random_uuid(),
    assessment_number  VARCHAR(20)  NOT NULL,
    patient_id         UUID         NOT NULL REFERENCES patients(id),
    asha_worker_id     UUID         NOT NULL REFERENCES users(id),
    patient_complaint  TEXT,
    complaint_category VARCHAR(50),
    status             VARCHAR(20)  NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT','SUBMITTED','AI_PROCESSING','COMPLETED','REFERRED')),
    risk_level         VARCHAR(10)
        CHECK (risk_level IS NULL OR risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    assessed_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    submitted_at       TIMESTAMPTZ,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by         VARCHAR(100),
    updated_by         VARCHAR(100),
    CONSTRAINT pk_assessments    PRIMARY KEY (id),
    CONSTRAINT uq_assessment_num UNIQUE (assessment_number)
);

CREATE TABLE symptoms (
    id            UUID         NOT NULL DEFAULT gen_random_uuid(),
    assessment_id UUID         NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    name          VARCHAR(200) NOT NULL,
    duration      VARCHAR(100),
    severity      VARCHAR(20),
    remarks       TEXT,
    CONSTRAINT pk_symptoms PRIMARY KEY (id)
);

CREATE TABLE vitals (
    id                        UUID          NOT NULL DEFAULT gen_random_uuid(),
    assessment_id             UUID          NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    heart_rate                INTEGER,
    spo2                      NUMERIC(5,2),
    temperature               NUMERIC(5,2),
    blood_pressure_systolic   INTEGER,
    blood_pressure_diastolic  INTEGER,
    respiratory_rate          INTEGER,
    height                    NUMERIC(6,2),
    weight                    NUMERIC(6,2),
    bmi                       NUMERIC(5,2),
    blood_sugar               NUMERIC(7,2),
    CONSTRAINT pk_vitals               PRIMARY KEY (id),
    CONSTRAINT uq_vitals_assessment_id UNIQUE (assessment_id)
);

CREATE TABLE medical_histories (
    id                   UUID NOT NULL DEFAULT gen_random_uuid(),
    assessment_id        UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    past_illnesses       TEXT,
    current_medications  TEXT,
    allergies            TEXT,
    family_history       TEXT,
    surgery_history      TEXT,
    habits               TEXT,
    CONSTRAINT pk_medical_histories               PRIMARY KEY (id),
    CONSTRAINT uq_medical_history_assessment_id   UNIQUE (assessment_id)
);

CREATE TABLE examination_findings (
    id                 UUID         NOT NULL DEFAULT gen_random_uuid(),
    assessment_id      UUID         NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    general_appearance TEXT,
    consciousness      VARCHAR(100),
    edema              TEXT,
    skin               TEXT,
    respiratory        TEXT,
    cardiovascular     TEXT,
    abdominal          TEXT,
    neurological       TEXT,
    CONSTRAINT pk_examination_findings               PRIMARY KEY (id),
    CONSTRAINT uq_examination_finding_assessment_id  UNIQUE (assessment_id)
);

CREATE TABLE legacy_information (
    id                       UUID NOT NULL DEFAULT gen_random_uuid(),
    assessment_id            UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    family_support           TEXT,
    living_conditions        TEXT,
    previous_interventions   TEXT,
    notes                    TEXT,
    CONSTRAINT pk_legacy_information               PRIMARY KEY (id),
    CONSTRAINT uq_legacy_information_assessment_id UNIQUE (assessment_id)
);

CREATE TABLE ai_assessment_results (
    id               UUID          NOT NULL DEFAULT gen_random_uuid(),
    assessment_id    UUID          NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    summary          TEXT,
    risk_level       VARCHAR(10)
        CHECK (risk_level IS NULL OR risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    confidence_score NUMERIC(5,4),
    recommendations  TEXT,
    generated_at     TIMESTAMPTZ,
    source           VARCHAR(100),
    CONSTRAINT pk_ai_assessment_results               PRIMARY KEY (id),
    CONSTRAINT uq_ai_assessment_result_assessment_id  UNIQUE (assessment_id)
);

-- ── Indexes ───────────────────────────────────────────────────────
CREATE INDEX idx_assessments_patient_id      ON assessments (patient_id);
CREATE INDEX idx_assessments_asha_worker_id  ON assessments (asha_worker_id);
CREATE INDEX idx_assessments_status          ON assessments (status);
CREATE INDEX idx_assessments_assessed_at     ON assessments (assessed_at DESC);
CREATE INDEX idx_symptoms_assessment_id      ON symptoms (assessment_id);
