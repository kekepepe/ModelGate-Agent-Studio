"""Reconcile model provider fields for legacy SQLite databases.

Revision ID: 0009_model_provider_fields
Revises: 0008_worktree_audit
"""

import sqlalchemy as sa

from alembic_helpers import add_column_if_missing

revision = "0009_model_provider_fields"
down_revision = "0008_worktree_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    add_column_if_missing("models", sa.Column("api_key", sa.Text(), nullable=True))
    add_column_if_missing("models", sa.Column("api_base_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    # Forward-repair policy: provider configuration remains intact.
    pass
