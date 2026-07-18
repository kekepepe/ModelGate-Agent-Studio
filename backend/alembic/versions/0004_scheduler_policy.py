"""Persist the Goal scheduler parallelism ceiling.

Revision ID: 0004_scheduler_policy
Revises: 0003_execution_plan
"""

from alembic_helpers import add_column_if_missing
import sqlalchemy as sa

revision = "0004_scheduler_policy"
down_revision = "0003_execution_plan"
branch_labels = None
depends_on = None


def upgrade() -> None:
    add_column_if_missing("goals", sa.Column("max_parallel_tasks", sa.Integer(), nullable=False, server_default=sa.text("3")))


def downgrade() -> None:
    # Forward-repair policy: scheduler policy is retained.
    pass
