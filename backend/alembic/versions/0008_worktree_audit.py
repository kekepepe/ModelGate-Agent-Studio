"""Persist auditable Git worktree and merge lifecycle metadata.

Revision ID: 0008_worktree_audit
Revises: 0007_runtime_recovery
"""

import sqlalchemy as sa

from alembic_helpers import add_column_if_missing, create_index_if_missing

revision = "0008_worktree_audit"
down_revision = "0007_runtime_recovery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for column in (
        sa.Column("base_commit_sha", sa.String(64), nullable=True),
        sa.Column("branch_name", sa.String(255), nullable=True),
        sa.Column("agent_id", sa.String(36), nullable=True),
        sa.Column("commit_sha", sa.String(64), nullable=True),
        sa.Column("merge_commit_sha", sa.String(64), nullable=True),
        sa.Column("merge_output", sa.Text(), nullable=True),
        sa.Column("conflict_files", sa.Text(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("merged_at", sa.DateTime(), nullable=True),
    ):
        add_column_if_missing("workspace_worktrees", column)
    create_index_if_missing("ix_workspace_worktrees_agent_id", "workspace_worktrees", ["agent_id"])
    create_index_if_missing("ux_workspace_worktrees_branch_name", "workspace_worktrees", ["branch_name"], unique=True)


def downgrade() -> None:
    # Forward-repair policy: branch and merge audit evidence is retained.
    pass
