"""MCP server registry + tool origin (V1.3 P3).

Per V1.3-plan.md §4: the Local Tool Runtime gains an external tool
platform. `mcp_servers` holds the registry (stdio transport first —
the MCP stdio framing is newline-delimited JSON-RPC and stable across
protocol revisions), and `tool_definitions.server_id` marks which
registered server a tool came from (NULL = built-in local tool).

Revision ID: 0014_mcp_servers
Revises: 0013_execution_log_cost
"""

import sqlalchemy as sa

from alembic import op
from alembic_helpers import add_column_if_missing, has_table

revision = "0014_mcp_servers"
down_revision = "0013_execution_log_cost"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not has_table("mcp_servers"):
        sa.Table(
            "mcp_servers",
            sa.MetaData(),
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("transport", sa.String(30), nullable=False, server_default="stdio"),
            sa.Column("command_or_url", sa.String(2000), nullable=False),
            sa.Column("args", sa.Text(), nullable=False, server_default="[]"),
            sa.Column("env_secrets", sa.Text(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("last_health", sa.String(30), nullable=True),
            sa.Column("last_health_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        ).create(op.get_bind())
    add_column_if_missing(
        "tool_definitions",
        sa.Column("server_id", sa.String(36), nullable=True),
    )


def downgrade() -> None:
    # Forward-repair policy: registry rows are inert once the application
    # layer stops reading them; keep data on downgrade.
    pass
