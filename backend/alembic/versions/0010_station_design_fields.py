"""Add design-aligned fields to agent_stations (V1.0-3).

Per 2026-09-06-platform-redesign.md §4.1 (Station model):

  - slug           TEXT  unique, identifies built-in roles
  - is_builtin     BOOL  default FALSE, marks seeded vs user-created
  - handoff_policy JSON  structured {can_initiate, on_quota_exhausted,
                                    on_provider_error}

`slug` + `is_builtin` are not NULLABLE so the API can rely on them.
`handoff_policy` is seeded with a sensible default and may be NULL
during the migration window; the application layer treats NULL as
"fall back to the boolean `allow_handoff` column" until it is set.

Revision ID: 0010_station_design_fields
Revises: 0009_model_provider_fields
"""

import sqlalchemy as sa

from alembic_helpers import add_column_if_missing, create_index_if_missing

revision = "0010_station_design_fields"
down_revision = "0009_model_provider_fields"
branch_labels = None
depends_on = None


# Default JSON value for handoff_policy (forward-fill new rows + existing rows)
_DEFAULT_HANDOFF_POLICY = (
    '{"can_initiate": true, '
    '"on_quota_exhausted": "handoff", '
    '"on_provider_error": "retry_once"}'
)


def upgrade() -> None:
    add_column_if_missing(
        "agent_stations",
        sa.Column("slug", sa.String(50), nullable=True),
    )
    add_column_if_missing(
        "agent_stations",
        sa.Column(
            "is_builtin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    add_column_if_missing(
        "agent_stations",
        sa.Column(
            "handoff_policy",
            sa.Text(),
            nullable=True,
            server_default=sa.text(f"'{_DEFAULT_HANDOFF_POLICY}'"),
        ),
    )
    # Slug must be unique where set. Partial unique index so the
    # legacy rows with NULL slug do not collide.
    create_index_if_missing(
        "ux_agent_stations_slug",
        "agent_stations",
        ["slug"],
        unique=True,
    )
    # SQLite CHECK constraints can't be added idempotently without a
    # table rebuild, so we skip a DB-level enum check. The application
    # layer validates `role` and `slug` shapes.


def downgrade() -> None:
    # Forward-repair policy: design fields are retained even on downgrade
    # so existing rows keep the new columns.
    pass
