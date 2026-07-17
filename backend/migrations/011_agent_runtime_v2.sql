-- Runtime v2: execution modes, dynamic task graph metadata and evidence.
ALTER TABLE goals ADD COLUMN execution_mode VARCHAR(20) NOT NULL DEFAULT 'live';
ALTER TABLE goals ADD COLUMN workspace_root TEXT;
ALTER TABLE goals ADD COLUMN run_id VARCHAR(36);
ALTER TABLE goals ADD COLUMN final_verification_status VARCHAR(50);
ALTER TABLE goals ADD COLUMN budget_tokens INTEGER NOT NULL DEFAULT 100000;
ALTER TABLE goals ADD COLUMN budget_cost_usd FLOAT;
ALTER TABLE goals ADD COLUMN max_duration_seconds INTEGER NOT NULL DEFAULT 3600;

ALTER TABLE tasks ADD COLUMN task_type VARCHAR(50) NOT NULL DEFAULT 'general';
ALTER TABLE tasks ADD COLUMN required_capabilities TEXT NOT NULL DEFAULT '[]';
ALTER TABLE tasks ADD COLUMN required_tools TEXT NOT NULL DEFAULT '[]';
ALTER TABLE tasks ADD COLUMN dependencies TEXT NOT NULL DEFAULT '[]';
ALTER TABLE tasks ADD COLUMN acceptance_criteria TEXT NOT NULL DEFAULT '[]';
ALTER TABLE tasks ADD COLUMN risk_level VARCHAR(20) NOT NULL DEFAULT 'low';
ALTER TABLE tasks ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE tasks ADD COLUMN max_retries INTEGER NOT NULL DEFAULT 2;
ALTER TABLE tasks ADD COLUMN verification_status VARCHAR(50);
ALTER TABLE tasks ADD COLUMN blocked_reason TEXT;
ALTER TABLE tasks ADD COLUMN parent_task_id VARCHAR(36);

CREATE TABLE IF NOT EXISTS artifacts (
    id VARCHAR(36) PRIMARY KEY, run_id VARCHAR(36), task_id VARCHAR(36) NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'file', path TEXT, checksum VARCHAR(128),
    verification_status VARCHAR(50), metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS verification_results (
    id VARCHAR(36) PRIMARY KEY, task_id VARCHAR(36) NOT NULL, criterion_type VARCHAR(50) NOT NULL,
    command_or_rule TEXT NOT NULL, status VARCHAR(50) NOT NULL, evidence TEXT, exit_code INTEGER,
    created_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS workspace_checkpoints (
    id VARCHAR(36) PRIMARY KEY, goal_id VARCHAR(36) NOT NULL, task_id VARCHAR(36) NOT NULL,
    path TEXT NOT NULL, existed BOOLEAN NOT NULL DEFAULT 0, content TEXT, checksum VARCHAR(128),
    created_at DATETIME NOT NULL
);
ALTER TABLE worker_sessions ADD COLUMN workspace_scope TEXT;
ALTER TABLE worker_sessions ADD COLUMN step_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE worker_sessions ADD COLUMN failure_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE worker_sessions ADD COLUMN last_observation TEXT;
ALTER TABLE worker_sessions ADD COLUMN next_action TEXT;
ALTER TABLE agent_stations ADD COLUMN max_tokens_per_task INTEGER NOT NULL DEFAULT 32000;
ALTER TABLE agent_stations ADD COLUMN max_duration_seconds INTEGER NOT NULL DEFAULT 900;
ALTER TABLE agent_stations ADD COLUMN max_consecutive_failures INTEGER NOT NULL DEFAULT 3;
ALTER TABLE tool_call_records ADD COLUMN result_data TEXT NOT NULL DEFAULT '{}';
ALTER TABLE memory_drafts ADD COLUMN expires_at DATETIME;
ALTER TABLE skill_drafts ADD COLUMN version VARCHAR(50) NOT NULL DEFAULT '1.0';
ALTER TABLE skill_drafts ADD COLUMN success_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE skill_drafts ADD COLUMN failure_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE skill_drafts ADD COLUMN last_used_at DATETIME;
CREATE TABLE IF NOT EXISTS workspace_worktrees (
    id VARCHAR(36) PRIMARY KEY, goal_id VARCHAR(36) NOT NULL, task_id VARCHAR(36) NOT NULL UNIQUE,
    path TEXT NOT NULL UNIQUE, base_ref VARCHAR(255) NOT NULL DEFAULT 'HEAD', status VARCHAR(30) NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL, removed_at DATETIME
);
CREATE TABLE IF NOT EXISTS runtime_runs (
    id VARCHAR(36) PRIMARY KEY, goal_id VARCHAR(36) NOT NULL, execution_mode VARCHAR(20) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'running', started_at DATETIME NOT NULL, ended_at DATETIME,
    final_verification_status VARCHAR(50), budget_tokens INTEGER NOT NULL DEFAULT 100000,
    budget_cost_usd FLOAT, max_duration_seconds INTEGER NOT NULL DEFAULT 3600
);
