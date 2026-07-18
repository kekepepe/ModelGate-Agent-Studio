-- Runtime P0-1: immutable ExecutionPlan versions and task provenance.
CREATE TABLE IF NOT EXISTS execution_plans (
    id VARCHAR(36) PRIMARY KEY,
    plan_id VARCHAR(36) NOT NULL,
    goal_id VARCHAR(36) NOT NULL,
    version INTEGER NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'validated',
    task_mode VARCHAR(40) NOT NULL,
    goal_summary TEXT NOT NULL,
    assumptions TEXT NOT NULL DEFAULT '[]',
    required_context TEXT NOT NULL DEFAULT '[]',
    activation_reason TEXT NOT NULL,
    final_acceptance_criteria TEXT NOT NULL DEFAULT '[]',
    human_approval_points TEXT NOT NULL DEFAULT '[]',
    estimated_cost TEXT NOT NULL DEFAULT '{}',
    fallback_reason TEXT,
    planner_type VARCHAR(30) NOT NULL DEFAULT 'rule_fallback',
    raw_output TEXT,
    repair_records TEXT NOT NULL DEFAULT '[]',
    created_at DATETIME NOT NULL,
    confirmed_at DATETIME,
    CONSTRAINT uq_execution_plan_goal_version UNIQUE (goal_id, version),
    CONSTRAINT uq_execution_plan_id_version UNIQUE (plan_id, version)
);

CREATE INDEX IF NOT EXISTS ix_execution_plans_plan_id ON execution_plans(plan_id);
CREATE INDEX IF NOT EXISTS ix_execution_plans_goal_id ON execution_plans(goal_id);
CREATE INDEX IF NOT EXISTS ix_execution_plans_status ON execution_plans(status);

CREATE TABLE IF NOT EXISTS plan_tasks (
    id VARCHAR(36) PRIMARY KEY,
    plan_version_id VARCHAR(36) NOT NULL,
    client_task_id VARCHAR(100) NOT NULL,
    objective TEXT NOT NULL,
    task_type VARCHAR(30) NOT NULL,
    required_capabilities TEXT NOT NULL DEFAULT '[]',
    required_tools TEXT NOT NULL DEFAULT '[]',
    dependencies TEXT NOT NULL DEFAULT '[]',
    acceptance_criteria TEXT NOT NULL DEFAULT '[]',
    risk_level VARCHAR(20) NOT NULL DEFAULT 'low',
    parallel_safe BOOLEAN NOT NULL DEFAULT 0,
    context_query TEXT NOT NULL DEFAULT '',
    approval_required BOOLEAN NOT NULL DEFAULT 0,
    workspace_scope TEXT,
    merge_strategy TEXT,
    runtime_task_id VARCHAR(36),
    source VARCHAR(30) NOT NULL DEFAULT 'created',
    created_at DATETIME NOT NULL,
    CONSTRAINT uq_plan_task_client_id UNIQUE (plan_version_id, client_task_id)
);

CREATE INDEX IF NOT EXISTS ix_plan_tasks_plan_version_id ON plan_tasks(plan_version_id);
CREATE INDEX IF NOT EXISTS ix_plan_tasks_runtime_task_id ON plan_tasks(runtime_task_id);

CREATE TABLE IF NOT EXISTS plan_changes (
    id VARCHAR(36) PRIMARY KEY,
    goal_id VARCHAR(36) NOT NULL,
    from_plan_version_id VARCHAR(36),
    to_plan_version_id VARCHAR(36) NOT NULL,
    change_type VARCHAR(30) NOT NULL DEFAULT 'created',
    reason TEXT NOT NULL,
    evidence TEXT NOT NULL DEFAULT '[]',
    retained_task_ids TEXT NOT NULL DEFAULT '[]',
    cancelled_task_ids TEXT NOT NULL DEFAULT '[]',
    added_task_ids TEXT NOT NULL DEFAULT '[]',
    replaced_task_ids TEXT NOT NULL DEFAULT '[]',
    created_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_plan_changes_goal_id ON plan_changes(goal_id);
CREATE INDEX IF NOT EXISTS ix_plan_changes_from_plan_version_id ON plan_changes(from_plan_version_id);
CREATE INDEX IF NOT EXISTS ix_plan_changes_to_plan_version_id ON plan_changes(to_plan_version_id);

ALTER TABLE tasks ADD COLUMN plan_version_id VARCHAR(36);
ALTER TABLE tasks ADD COLUMN plan_task_id VARCHAR(36);
ALTER TABLE tasks ADD COLUMN plan_source VARCHAR(30);
