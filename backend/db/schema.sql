-- SQLite schema for the IT Application Knowledge Graph
-- Run via: python -m backend.db.init_schema

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────
-- Node Tables
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS applications (
    application_id       TEXT PRIMARY KEY,
    application_name     TEXT NOT NULL,
    company              TEXT,
    publisher            TEXT,
    description          TEXT,
    updated              TEXT,
    last_updated_by      TEXT,          -- PII: display only, never embed or send to AI
    business_owner       TEXT,          -- PII
    td_app_owner         TEXT,          -- PII
    primary_engineer     TEXT,          -- PII
    support_group        TEXT,
    active               INTEGER,
    install_status       TEXT,
    application_url      TEXT,
    portfolio_manager    TEXT,
    application_type     TEXT,          -- 'COTS' | 'Homegrown' | NULL
    architecture_type    TEXT,
    baptist_managed      INTEGER,       -- 1 | 0 | NULL
    business_criticality TEXT,
    business_process     TEXT,
    environment          TEXT,
    active_status        INTEGER NOT NULL DEFAULT 1,  -- 0 = soft-deleted on refresh
    content_hash         TEXT           -- SHA-256(application_name + description) for incremental re-embedding
);

CREATE TABLE IF NOT EXISTS application_types (
    type_id   TEXT PRIMARY KEY,
    type_name TEXT NOT NULL UNIQUE      -- 'COTS' | 'Homegrown'
);

CREATE TABLE IF NOT EXISTS architecture_types (
    arch_id   TEXT PRIMARY KEY,
    arch_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS business_processes (
    process_id   TEXT PRIMARY KEY,
    process_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS companies (
    company_id   TEXT PRIMARY KEY,
    company_name TEXT NOT NULL UNIQUE
);

-- ─────────────────────────────────────────────
-- Edge Tables (Graph Layer)
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS app_uses_type (
    application_id TEXT NOT NULL REFERENCES applications(application_id),
    type_id        TEXT NOT NULL REFERENCES application_types(type_id),
    PRIMARY KEY (application_id, type_id)
);

CREATE TABLE IF NOT EXISTS app_has_architecture (
    application_id TEXT NOT NULL REFERENCES applications(application_id),
    arch_id        TEXT NOT NULL REFERENCES architecture_types(arch_id),
    PRIMARY KEY (application_id, arch_id)
);

CREATE TABLE IF NOT EXISTS app_supports_process (
    application_id TEXT NOT NULL REFERENCES applications(application_id),
    process_id     TEXT NOT NULL REFERENCES business_processes(process_id),
    PRIMARY KEY (application_id, process_id)
);

-- ─────────────────────────────────────────────
-- ETL Audit Trail
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS etl_runs (
    run_id          TEXT PRIMARY KEY,
    run_at          TEXT NOT NULL,      -- ISO 8601
    xlsx_hash       TEXT,               -- SHA-256 of uploaded XLSX file
    records_loaded  INTEGER,
    records_skipped INTEGER,
    status          TEXT NOT NULL,      -- 'success' | 'partial' | 'failed'
    error_detail    TEXT                -- JSON array of {application_name, company, reason}
);

-- ─────────────────────────────────────────────
-- Indexes (active records only — partial indexes for performance)
-- ─────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_applications_type
    ON applications(application_type) WHERE active_status = 1;

CREATE INDEX IF NOT EXISTS idx_applications_company
    ON applications(company) WHERE active_status = 1;

CREATE INDEX IF NOT EXISTS idx_applications_baptist_managed
    ON applications(baptist_managed) WHERE active_status = 1;

CREATE INDEX IF NOT EXISTS idx_applications_name
    ON applications(application_name) WHERE active_status = 1;

CREATE INDEX IF NOT EXISTS idx_applications_business_process
    ON applications(business_process) WHERE active_status = 1;

CREATE INDEX IF NOT EXISTS idx_app_supports_process_process
    ON app_supports_process(process_id);

CREATE INDEX IF NOT EXISTS idx_app_uses_type_type
    ON app_uses_type(type_id);

CREATE INDEX IF NOT EXISTS idx_etl_runs_run_at
    ON etl_runs(run_at DESC);
