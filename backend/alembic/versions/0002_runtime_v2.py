"""Reconcile Runtime V2 columns for legacy databases.

Revision ID: 0002_runtime_v2
Revises: 0001_schema_baseline
"""

from alembic_helpers import add_column_if_missing, create_index_if_missing
import sqlalchemy as sa

revision = "0002_runtime_v2"
down_revision = "0001_schema_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name, column_type, default in (
        ("execution_mode", sa.String(20), "'live'"),
        ("budget_tokens", sa.Integer(), "100000"),
        ("max_duration_seconds", sa.Integer(), "3600"),
    ):
        add_column_if_missing("goals", sa.Column(name, column_type, nullable=False, server_default=sa.text(default)))
    for name, column_type in (
        ("workspace_root", sa.Text()),
        ("run_id", sa.String(36)),
        ("final_verification_status", sa.String(50)),
        ("budget_cost_usd", sa.Float()),
    ):
        add_column_if_missing("goals", sa.Column(name, column_type, nullable=True))

    task_columns = (
        ("task_type", sa.String(50), "'general'"),
        ("required_capabilities", sa.Text(), "'[]'"),
        ("required_tools", sa.Text(), "'[]'"),
        ("dependencies", sa.Text(), "'[]'"),
        ("acceptance_criteria", sa.Text(), "'[]'"),
        ("risk_level", sa.String(20), "'low'"),
        ("retry_count", sa.Integer(), "0"),
        ("max_retries", sa.Integer(), "2"),
    )
    for name, column_type, default in task_columns:
        add_column_if_missing("tasks", sa.Column(name, column_type, nullable=False, server_default=sa.text(default)))
    for name, column_type in (
        ("verification_status", sa.String(50)),
        ("blocked_reason", sa.Text()),
        ("parent_task_id", sa.String(36)),
    ):
        add_column_if_missing("tasks", sa.Column(name, column_type, nullable=True))

    for name, column_type, default in (
        ("step_count", sa.Integer(), "0"),
        ("failure_count", sa.Integer(), "0"),
    ):
        add_column_if_missing("worker_sessions", sa.Column(name, column_type, nullable=False, server_default=sa.text(default)))
    for name in ("workspace_scope", "last_observation", "next_action"):
        add_column_if_missing("worker_sessions", sa.Column(name, sa.Text(), nullable=True))

    for name, default in (
        ("max_tokens_per_task", "32000"),
        ("max_duration_seconds", "900"),
        ("max_consecutive_failures", "3"),
    ):
        add_column_if_missing("agent_stations", sa.Column(name, sa.Integer(), nullable=False, server_default=sa.text(default)))
    add_column_if_missing("tool_call_records", sa.Column("result_data", sa.Text(), nullable=False, server_default=sa.text("'{}'")))
    add_column_if_missing("memory_drafts", sa.Column("expires_at", sa.DateTime(), nullable=True))
    for name, column_type, default in (
        ("version", sa.String(50), "'1.0'"),
        ("success_count", sa.Integer(), "0"),
        ("failure_count", sa.Integer(), "0"),
    ):
        add_column_if_missing("skill_drafts", sa.Column(name, column_type, nullable=False, server_default=sa.text(default)))
    add_column_if_missing("skill_drafts", sa.Column("last_used_at", sa.DateTime(), nullable=True))
    create_index_if_missing("ix_goals_run_id", "goals", ["run_id"])
    create_index_if_missing("ix_tasks_parent_task_id", "tasks", ["parent_task_id"])


def downgrade() -> None:
    # Forward-repair policy: legacy data columns are retained on rollback.
    pass
