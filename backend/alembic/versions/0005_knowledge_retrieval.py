"""Mark the Knowledge/Retrieval schema milestone.

Revision ID: 0005_knowledge_retrieval
Revises: 0004_scheduler_policy
"""

revision = "0005_knowledge_retrieval"
down_revision = "0004_scheduler_policy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The portable baseline creates absent knowledge tables with all current
    # constraints. This checkpoint keeps the historical milestone versioned.
    pass


def downgrade() -> None:
    # Forward-repair policy: indexed knowledge remains intact.
    pass
