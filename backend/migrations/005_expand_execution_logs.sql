-- Migration 005: Expand execution_logs table for Logs/Observability module
-- Drops the minimal stub table from 004 and recreates with full schema.
-- NOTE: This will LOSE any existing execution_logs data. Current logs are only
-- internal handoff traces and can be regenerated.

DROP TABLE IF EXISTS execution_logs;

CREATE TABLE execution_logs (
    id VARCHAR(36) PRIMARY KEY,
    goal_id VARCHAR(36),
    task_id VARCHAR(36),
    agent_id VARCHAR(36),
    worker_id VARCHAR(36),
    model_id VARCHAR(100),
    handoff_id VARCHAR(36),
    event_type VARCHAR(50) NOT NULL,
    event_status VARCHAR(50) NOT NULL,
    input_summary TEXT,
    output_summary TEXT,
    token_usage TEXT,
    latency_ms INTEGER,
    error_type VARCHAR(50),
    error_code VARCHAR(50),
    error_message TEXT,
    tool_name VARCHAR(100),
    quota_status VARCHAR(50),
    handoff_status VARCHAR(50),
    extra_metadata TEXT,
    routing_info TEXT,
    created_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_execution_logs_goal_id ON execution_logs(goal_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_task_id ON execution_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_agent_id ON execution_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_model_id ON execution_logs(model_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_handoff_id ON execution_logs(handoff_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_event_type ON execution_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_execution_logs_event_status ON execution_logs(event_status);
CREATE INDEX IF NOT EXISTS idx_execution_logs_created_at ON execution_logs(created_at);
