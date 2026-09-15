"""Per-call cost column on execution_logs (V1.3 P2 T4).

0012 added pricing to models and total_cost_usd to quota_records. This
migration lets every model_call log carry its own USD cost so a
FinalSummary can aggregate real per-goal spend (SUM over the goal's
model_call logs) instead of the previous "cost unavailable" stance.

Revision ID: 0013_execution_log_cost
Revises: 0012_model_pricing
"""

import sqlalchemy as sa

from alembic_helpers import add_column_if_missing

revision = "0013_execution_log_cost"
down_revision = "0012_model_pricing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    add_column_if_missing(
        "execution_logs",
        sa.Column("cost_usd", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    # Forward-repair policy: derived cost data is kept even on downgrade.
    pass
