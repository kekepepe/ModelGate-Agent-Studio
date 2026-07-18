"""Reconcile capability registry fields for legacy Agent records.

Revision ID: 0006_capability_registry
Revises: 0005_knowledge_retrieval
"""

from alembic_helpers import add_column_if_missing
import sqlalchemy as sa

revision = "0006_capability_registry"
down_revision = "0005_knowledge_retrieval"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name, column_type, default in (
        ("capability_profile", sa.Text(), "'{}'"),
        ("workspace_permissions", sa.Text(), "'[]'"),
        ("input_types", sa.Text(), "'[\"text\"]'"),
        ("output_types", sa.Text(), "'[\"text\"]'"),
        ("max_concurrency", sa.Integer(), "1"),
    ):
        add_column_if_missing("agent_stations", sa.Column(name, column_type, nullable=False, server_default=sa.text(default)))
    add_column_if_missing("agent_stations", sa.Column("average_duration_ms", sa.Integer(), nullable=True))
    add_column_if_missing("agent_stations", sa.Column("average_cost_usd", sa.Float(), nullable=True))


def downgrade() -> None:
    # Forward-repair policy: capability history remains intact.
    pass
