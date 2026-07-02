-- Migration 009: Create tool_definitions and tool_call_records tables
-- MCP Tool Layer MVP.

CREATE TABLE IF NOT EXISTS tool_definitions (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category VARCHAR(50) NOT NULL DEFAULT '其他',
    risk_level VARCHAR(10) NOT NULL DEFAULT 'low' CHECK(risk_level IN ('low', 'medium', 'high')),
    parameters TEXT NOT NULL DEFAULT '{}',
    is_enabled BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tool_defs_name ON tool_definitions(name);
CREATE INDEX IF NOT EXISTS idx_tool_defs_category ON tool_definitions(category);
CREATE INDEX IF NOT EXISTS idx_tool_defs_enabled ON tool_definitions(is_enabled);

CREATE TABLE IF NOT EXISTS tool_call_records (
    id VARCHAR(36) PRIMARY KEY,
    goal_id VARCHAR(36),
    task_id VARCHAR(36),
    agent_id VARCHAR(36),
    worker_id VARCHAR(36),
    tool_name VARCHAR(100) NOT NULL,
    tool_input TEXT NOT NULL DEFAULT '{}',
    tool_output TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'started' CHECK(status IN ('started', 'completed', 'failed')),
    latency_ms INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_goal ON tool_call_records(goal_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_task ON tool_call_records(task_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_agent ON tool_call_records(agent_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_tool_name ON tool_call_records(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_calls_created ON tool_call_records(created_at);
