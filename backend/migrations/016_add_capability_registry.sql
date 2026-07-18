-- P2 capability-based Agent selection and historical operating limits.
ALTER TABLE agent_stations ADD COLUMN capability_profile TEXT NOT NULL DEFAULT '{}';
ALTER TABLE agent_stations ADD COLUMN workspace_permissions TEXT NOT NULL DEFAULT '[]';
ALTER TABLE agent_stations ADD COLUMN input_types TEXT NOT NULL DEFAULT '["text"]';
ALTER TABLE agent_stations ADD COLUMN output_types TEXT NOT NULL DEFAULT '["text"]';
ALTER TABLE agent_stations ADD COLUMN max_concurrency INTEGER NOT NULL DEFAULT 1;
ALTER TABLE agent_stations ADD COLUMN average_duration_ms INTEGER;
ALTER TABLE agent_stations ADD COLUMN average_cost_usd FLOAT;

CREATE TABLE IF NOT EXISTS agent_selection_decisions (
 id VARCHAR(36) PRIMARY KEY, goal_id VARCHAR(36), task_id VARCHAR(100) NOT NULL,
 required_capabilities TEXT NOT NULL DEFAULT '[]', required_tools TEXT NOT NULL DEFAULT '[]',
 candidates TEXT NOT NULL DEFAULT '[]', selected_agent_id VARCHAR(36) NOT NULL,
 selected_model_id VARCHAR(36) NOT NULL, backup_model_ids TEXT NOT NULL DEFAULT '[]',
 score FLOAT NOT NULL, selection_reason TEXT NOT NULL, fallback_entry TEXT NOT NULL DEFAULT '{}',
 created_at DATETIME NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_agent_selection_goal_id ON agent_selection_decisions(goal_id);
CREATE INDEX IF NOT EXISTS ix_agent_selection_task_id ON agent_selection_decisions(task_id);
CREATE INDEX IF NOT EXISTS ix_agent_selection_agent_id ON agent_selection_decisions(selected_agent_id);
CREATE INDEX IF NOT EXISTS ix_agent_selection_model_id ON agent_selection_decisions(selected_model_id);
CREATE INDEX IF NOT EXISTS ix_agent_selection_created_at ON agent_selection_decisions(created_at);
