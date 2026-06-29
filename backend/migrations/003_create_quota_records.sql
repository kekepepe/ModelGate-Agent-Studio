-- Migration: Create quota_records table for Quota Manager
-- Created: 2026-06-29

CREATE TABLE IF NOT EXISTS quota_records (
    id VARCHAR(36) PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    model_id VARCHAR(36) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 0,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    limit_error_count INTEGER NOT NULL DEFAULT 0,
    handoff_triggered_count INTEGER NOT NULL DEFAULT 0,
    quota_mode VARCHAR(20) NOT NULL DEFAULT 'unknown',
    token_limit INTEGER,
    request_limit INTEGER,
    cost_limit REAL,
    reset_period VARCHAR(20),
    reset_date INTEGER,
    usage_percent REAL,
    estimated_remaining INTEGER,
    quota_status VARCHAR(20) NOT NULL DEFAULT 'unknown',
    last_used_at DATETIME,
    cooldown_until DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_quota_provider_model ON quota_records(provider, model_id);
CREATE INDEX IF NOT EXISTS idx_quota_status ON quota_records(quota_status);
CREATE INDEX IF NOT EXISTS idx_quota_usage_percent ON quota_records(usage_percent);
