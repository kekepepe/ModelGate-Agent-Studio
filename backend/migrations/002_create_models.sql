-- Migration: Create models table for Model Router
-- Created: 2026-06-27

CREATE TABLE IF NOT EXISTS models (
    id VARCHAR(36) PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    capability_tags TEXT NOT NULL DEFAULT '[]',
    max_context_tokens INTEGER NOT NULL DEFAULT 8192,
    cost_level INTEGER NOT NULL DEFAULT 3,
    speed_level INTEGER NOT NULL DEFAULT 3,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider);
CREATE INDEX IF NOT EXISTS idx_models_is_enabled ON models(is_enabled);
CREATE INDEX IF NOT EXISTS idx_models_model_name ON models(model_name);
