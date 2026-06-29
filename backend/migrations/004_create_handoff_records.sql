CREATE TABLE IF NOT EXISTS handoff_records (
    id VARCHAR(36) PRIMARY KEY,
    goal_id VARCHAR(36) NOT NULL,
    task_id VARCHAR(36) NOT NULL,
    from_agent_id VARCHAR(36) NOT NULL,
    from_model_id VARCHAR(100) NOT NULL,
    from_worker_id VARCHAR(36),
    to_agent_id VARCHAR(36) NOT NULL,
    to_model_id VARCHAR(100) NOT NULL,
    to_worker_id VARCHAR(36),
    reason VARCHAR(50) NOT NULL,
    reason_description TEXT,
    handoff_summary TEXT NOT NULL DEFAULT '{}',
    status VARCHAR(50) NOT NULL DEFAULT 'requested',
    result_after_handoff VARCHAR(20),
    result_note TEXT,
    tokens_before_handoff INTEGER NOT NULL DEFAULT 0,
    tokens_after_handoff INTEGER NOT NULL DEFAULT 0,
    time_saved_estimate_ms INTEGER,
    error_message TEXT,
    created_at DATETIME NOT NULL,
    summary_generated_at DATETIME,
    accepted_at DATETIME,
    completed_at DATETIME,
    updated_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_handoff_task_status ON handoff_records(task_id, status);
CREATE INDEX IF NOT EXISTS idx_handoff_goal_id ON handoff_records(goal_id);
CREATE INDEX IF NOT EXISTS idx_handoff_from_agent_id ON handoff_records(from_agent_id);
CREATE INDEX IF NOT EXISTS idx_handoff_to_agent_id ON handoff_records(to_agent_id);
CREATE INDEX IF NOT EXISTS idx_handoff_created_at ON handoff_records(created_at);

CREATE TABLE IF NOT EXISTS handoff_tasks (
    id VARCHAR(36) PRIMARY KEY,
    goal_id VARCHAR(36) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    assigned_agent_id VARCHAR(36) NOT NULL,
    assigned_model_id VARCHAR(100) NOT NULL,
    assigned_worker_id VARCHAR(36),
    current_output TEXT,
    error_message TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_handoff_tasks_goal_id ON handoff_tasks(goal_id);
CREATE INDEX IF NOT EXISTS idx_handoff_tasks_status ON handoff_tasks(status);

CREATE TABLE IF NOT EXISTS worker_sessions (
    id VARCHAR(36) PRIMARY KEY,
    agent_id VARCHAR(36) NOT NULL,
    model_id VARCHAR(100) NOT NULL,
    goal_id VARCHAR(36) NOT NULL,
    task_id VARCHAR(36) NOT NULL,
    inherited_from_handoff_id VARCHAR(36),
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    current_context TEXT,
    final_output TEXT,
    error_message TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_worker_sessions_task_id ON worker_sessions(task_id);
CREATE INDEX IF NOT EXISTS idx_worker_sessions_handoff_id ON worker_sessions(inherited_from_handoff_id);

CREATE TABLE IF NOT EXISTS execution_logs (
    id VARCHAR(36) PRIMARY KEY,
    goal_id VARCHAR(36),
    task_id VARCHAR(36),
    agent_id VARCHAR(36),
    worker_id VARCHAR(36),
    model_id VARCHAR(100),
    handoff_id VARCHAR(36),
    level VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_execution_logs_goal_id ON execution_logs(goal_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_task_id ON execution_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_handoff_id ON execution_logs(handoff_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_created_at ON execution_logs(created_at);
