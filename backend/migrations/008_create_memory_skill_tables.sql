-- Migration 008: Create memory_drafts and skill_drafts tables
-- Memory / RAG / Skill self-evolution MVP.

CREATE TABLE IF NOT EXISTS memory_drafts (
    id VARCHAR(36) PRIMARY KEY,
    source_run_id VARCHAR(36),
    source_goal_id VARCHAR(36),
    type VARCHAR(50) NOT NULL DEFAULT 'project_memory',
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.5,
    reason TEXT,
    tags TEXT NOT NULL DEFAULT '[]',
    human_approved BOOLEAN,
    approved_by VARCHAR(100),
    approved_at DATETIME,
    extra_metadata TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_memory_drafts_type ON memory_drafts(type);
CREATE INDEX IF NOT EXISTS idx_memory_drafts_goal_id ON memory_drafts(source_goal_id);
CREATE INDEX IF NOT EXISTS idx_memory_drafts_approved ON memory_drafts(human_approved);

CREATE TABLE IF NOT EXISTS skill_drafts (
    id VARCHAR(36) PRIMARY KEY,
    source_run_id VARCHAR(36),
    name VARCHAR(255) NOT NULL,
    scenario TEXT,
    input_requirements TEXT,
    steps TEXT NOT NULL DEFAULT '[]',
    recommended_agents TEXT NOT NULL DEFAULT '[]',
    recommended_models TEXT NOT NULL DEFAULT '[]',
    tools TEXT NOT NULL DEFAULT '[]',
    output_format TEXT,
    success_criteria TEXT,
    common_failures TEXT NOT NULL DEFAULT '[]',
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    human_approved BOOLEAN,
    approved_by VARCHAR(100),
    approved_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_skill_drafts_status ON skill_drafts(status);
CREATE INDEX IF NOT EXISTS idx_skill_drafts_run_id ON skill_drafts(source_run_id);
