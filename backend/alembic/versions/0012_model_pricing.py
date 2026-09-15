"""Model pricing columns + quota cost accounting (V1.3 P2).

Per V1.3-plan.md §3 T1/T4: real multi-provider requires priceable models.

  - models.price_input / models.price_output   USD per 1M tokens (nullable —
    an unpriced model keeps FinalSummary cost.available=False instead of
    inventing numbers)
  - quota_records.total_cost_usd               running cost sum for the record

Revision ID: 0012_model_pricing
Revises: 0011_memory_skill_embeddings
"""

import sqlalchemy as sa

from alembic_helpers import add_column_if_missing

revision = "0012_model_pricing"
down_revision = "0011_memory_skill_embeddings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    add_column_if_missing(
        "models",
        sa.Column("price_input", sa.Float(), nullable=True),
    )
    add_column_if_missing(
        "models",
        sa.Column("price_output", sa.Float(), nullable=True),
    )
    add_column_if_missing(
        "quota_records",
        sa.Column("total_cost_usd", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    # Forward-repair policy: pricing data is kept even on downgrade.
    pass
