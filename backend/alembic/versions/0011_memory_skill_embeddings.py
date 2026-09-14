"""Embedding columns for memory_drafts and skill_drafts (V1.2).

Per V1.2-Memory-RAG-Skill-plan.md D2: memories and skills join the RAG
pipeline by storing their embedding vector (JSON list, same convention as
knowledge_chunks.embedding) plus the fingerprint of the adapter that
produced it. A fingerprint mismatch means the vector is stale and must be
re-embedded lazily (memory_vector_service.ensure_*).

Revision ID: 0011_memory_skill_embeddings
Revises: 0010_station_design_fields
"""

import sqlalchemy as sa

from alembic_helpers import add_column_if_missing

revision = "0011_memory_skill_embeddings"
down_revision = "0010_station_design_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    add_column_if_missing(
        "memory_drafts",
        sa.Column("embedding", sa.Text(), nullable=True),
    )
    add_column_if_missing(
        "memory_drafts",
        sa.Column("embedding_fingerprint", sa.String(100), nullable=True),
    )
    add_column_if_missing(
        "skill_drafts",
        sa.Column("embedding", sa.Text(), nullable=True),
    )
    add_column_if_missing(
        "skill_drafts",
        sa.Column("embedding_fingerprint", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    # Forward-repair policy: vectors are derived data and are kept even on
    # downgrade; they are inert without the application layer.
    pass
