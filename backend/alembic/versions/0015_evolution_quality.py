"""Evolution quality-loop columns (V1.5 QL1).

Per V1.5-plan.md §2:

  - memory_drafts.effectiveness_success / _failure: outcome votes from the
    tasks whose context actually carried this memory (same shape as the
    skill success counters); drives the hybrid-ranking weight.
  - memory_drafts.conflict_state: none | conflict | resolved — conflicting
    resolutions are marked for human adjudication, never auto-deleted.
  - retrieved_context_items.outcome: used | ignored — written back at task
    end (the legacy boolean `used` column keeps its retrieval-time meaning
    for compatibility).

Revision ID: 0015_evolution_quality
Revises: 0014_mcp_servers
"""

import sqlalchemy as sa

from alembic_helpers import add_column_if_missing

revision = "0015_evolution_quality"
down_revision = "0014_mcp_servers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    add_column_if_missing(
        "memory_drafts",
        sa.Column("effectiveness_success", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    add_column_if_missing(
        "memory_drafts",
        sa.Column("effectiveness_failure", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    add_column_if_missing(
        "memory_drafts",
        sa.Column("conflict_state", sa.String(20), nullable=True),
    )
    add_column_if_missing(
        "retrieved_context_items",
        sa.Column("outcome", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    # Forward-repair policy: outcome/quality data is kept even on downgrade.
    pass
