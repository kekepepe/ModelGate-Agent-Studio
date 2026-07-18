"""Add task leases and tool idempotency keys.

Revision ID: 0007_runtime_recovery
Revises: 0006_capability_registry
"""

from alembic_helpers import add_column_if_missing, create_index_if_missing
import sqlalchemy as sa

revision = "0007_runtime_recovery"
down_revision = "0006_capability_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    add_column_if_missing("tasks", sa.Column("lease_expires_at", sa.DateTime(), nullable=True))
    add_column_if_missing("tasks", sa.Column("recovery_count", sa.Integer(), nullable=False, server_default=sa.text("0")))
    add_column_if_missing("tool_call_records", sa.Column("idempotency_key", sa.String(64), nullable=True))
    create_index_if_missing("ix_tasks_lease_expires_at", "tasks", ["lease_expires_at"])
    create_index_if_missing("ix_tool_call_records_idempotency_key", "tool_call_records", ["idempotency_key"], unique=True)


def downgrade() -> None:
    # Forward-repair policy: recovery metadata is retained for auditability.
    pass
