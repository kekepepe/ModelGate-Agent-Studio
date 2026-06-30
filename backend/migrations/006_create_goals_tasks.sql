-- Migration 006: Create goals + tasks tables, extend worker_sessions
-- Agent Workspace module data foundation.

CREATE TABLE IF NOT EXISTS goals (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'idle',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);

CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(36) PRIMARY KEY,
    goal_id VARCHAR(36) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    assigned_agent_id VARCHAR(36),
    assigned_worker_id VARCHAR(36),
    output TEXT,
    tokens_used INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER,
    priority INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_agent_id) REFERENCES agent_stations(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_goal_id ON tasks(goal_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_agent ON tasks(assigned_agent_id);

-- Add total_tokens_used to existing worker_sessions table
ALTER TABLE worker_sessions ADD COLUMN total_tokens_used INTEGER NOT NULL DEFAULT 0;
