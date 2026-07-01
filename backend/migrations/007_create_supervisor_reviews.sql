-- Migration 007: Create supervisor_reviews table
-- Supervisor Review module for post-execution quality assessment.

CREATE TABLE IF NOT EXISTS supervisor_reviews (
    id VARCHAR(36) PRIMARY KEY,
    goal_id VARCHAR(36) NOT NULL,
    run_id VARCHAR(36),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    summary TEXT,
    issues TEXT NOT NULL DEFAULT '[]',
    suggested_tasks TEXT NOT NULL DEFAULT '[]',
    passed BOOLEAN NOT NULL DEFAULT FALSE,
    reviewer_agent_id VARCHAR(36),
    reviewer_model_id VARCHAR(100),
    tokens_used INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_supervisor_reviews_goal_id ON supervisor_reviews(goal_id);
CREATE INDEX IF NOT EXISTS idx_supervisor_reviews_status ON supervisor_reviews(status);
