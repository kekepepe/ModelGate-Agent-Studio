-- Migration: Add api_key and api_base_url to models table
-- Created: 2026-07-03

ALTER TABLE models ADD COLUMN api_key TEXT DEFAULT NULL;
ALTER TABLE models ADD COLUMN api_base_url VARCHAR(500) DEFAULT NULL;
