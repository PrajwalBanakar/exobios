-- ─────────────────────────────────────────────────────────────────────────────
-- V2 : Seed development users
-- Safe to re-run: ON CONFLICT (phone) DO NOTHING skips existing rows.
-- Passwords hashed with BCrypt cost 12.
--   SUPER_ADMIN : Admin@123
--   ASHA        : Asha@123
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO users (phone, name, password_hash, role, status, created_by, updated_by)
VALUES ('9999999999', 'Super Admin',
        '$2a$12$mi7cFv0dIvEsGnI9ZRs6SuBp9eV9vwyGfBV9pRDiGL9FnvepodNLO',
        'SUPER_ADMIN', 'ACTIVE', 'SYSTEM', 'SYSTEM')
ON CONFLICT (phone) DO NOTHING;

INSERT INTO users (asha_id, phone, name, password_hash, role, area, district, state, status, created_by, updated_by)
VALUES ('ASHA001', '9876543210', 'Demo ASHA Worker',
        '$2a$12$Ca5JY4tjt3kLCqNitdnkFeGb90is2x2bhxjPgbHu.aELZqqE4YUZi',
        'ASHA', 'Demo Area', 'Demo District', 'Karnataka', 'ACTIVE', 'SYSTEM', 'SYSTEM')
ON CONFLICT (phone) DO NOTHING;
