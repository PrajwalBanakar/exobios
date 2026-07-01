-- ─────────────────────────────────────────────────────────────────────────────
-- V9 — Widen SMALLINT columns to INTEGER to match JPA entity mappings.
-- PostgreSQL allows lossless SMALLINT → INTEGER widening; existing CHECK
-- constraints and data are preserved automatically.
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE devices ALTER COLUMN battery_level TYPE INTEGER;
ALTER TABLE feedback ALTER COLUMN rating        TYPE INTEGER;
