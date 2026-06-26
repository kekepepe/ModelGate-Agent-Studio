CREATE TABLE IF NOT EXISTS agent_stations (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'idle',
    current_task_id VARCHAR(36),
    default_model_id VARCHAR(36) NOT NULL,
    backup_model_ids TEXT NOT NULL DEFAULT '[]',
    allowed_tools TEXT NOT NULL DEFAULT '[]',
    system_prompt TEXT NOT NULL,
    output_format VARCHAR(50),
    max_steps_per_task INTEGER NOT NULL DEFAULT 10,
    max_tool_calls_per_task INTEGER DEFAULT 20,
    allow_handoff BOOLEAN NOT NULL DEFAULT false,
    handoff_threshold_tokens INTEGER,
    is_enabled BOOLEAN NOT NULL DEFAULT true,
    total_tasks_completed INTEGER NOT NULL DEFAULT 0,
    total_tasks_failed INTEGER NOT NULL DEFAULT 0,
    total_handoffs_initiated INTEGER NOT NULL DEFAULT 0,
    average_tokens_per_task INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_stations_role ON agent_stations(role);
CREATE INDEX IF NOT EXISTS idx_agent_stations_status ON agent_stations(status);
CREATE INDEX IF NOT EXISTS idx_agent_stations_is_enabled ON agent_stations(is_enabled);
CREATE INDEX IF NOT EXISTS idx_agent_stations_current_task_id ON agent_stations(current_task_id);
