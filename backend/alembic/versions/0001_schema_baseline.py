"""Create the portable current-schema baseline.

Revision ID: 0001_schema_baseline
Revises: None
"""

from alembic import op

from src.core.database import Base
from src.models import agent as _agent  # noqa: F401
from src.models import handoff as _handoff  # noqa: F401
from src.models import knowledge as _knowledge  # noqa: F401
from src.models import model as _model  # noqa: F401
from src.models import quota as _quota  # noqa: F401
from src.models import selection as _selection  # noqa: F401
from src.models import supervisor as _supervisor  # noqa: F401
from src.models import tool as _tool  # noqa: F401
from src.models import workspace as _workspace  # noqa: F401

revision = "0001_schema_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # checkfirst preserves legacy 001-012 tables while creating all tables that
    # do not yet exist. Later revisions reconcile missing legacy columns.
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    # Baseline downgrade is intentionally destructive and is reserved for
    # disposable environments. Production rollback uses backup restoration.
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=True)
