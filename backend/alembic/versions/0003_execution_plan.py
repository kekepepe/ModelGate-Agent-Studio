"""Reconcile ExecutionPlan provenance columns.

Revision ID: 0003_execution_plan
Revises: 0002_runtime_v2
"""

from alembic_helpers import add_column_if_missing, create_index_if_missing
import sqlalchemy as sa

revision = "0003_execution_plan"
down_revision = "0002_runtime_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    add_column_if_missing("tasks", sa.Column("plan_version_id", sa.String(36), nullable=True))
    add_column_if_missing("tasks", sa.Column("plan_task_id", sa.String(36), nullable=True))
    add_column_if_missing("tasks", sa.Column("plan_source", sa.String(30), nullable=True))
    create_index_if_missing("ix_tasks_plan_version_id", "tasks", ["plan_version_id"])
    create_index_if_missing("ix_tasks_plan_task_id", "tasks", ["plan_task_id"])


def downgrade() -> None:
    # Forward-repair policy: provenance is retained for auditability.
    pass
