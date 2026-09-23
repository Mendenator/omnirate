"""P2-10: pgvector extension + review_embeddings table.

Revision ID: 0007_review_embeddings
Revises: 0006_analytics_export_state
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "0007_review_embeddings"
down_revision = "0006_analytics_export_state"
branch_labels = None
depends_on = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "review_embeddings",
        sa.Column("review_id", UUID(as_uuid=True), sa.ForeignKey("reviews.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # IVFFlat index for approximate nearest-neighbor cosine search at scale;
    # `lists` is a starting point (rule of thumb: sqrt(row_count)) — the
    # cosine-distance similarity found in the SOW's clustering flow
    # (app/domain/embedding_service.py) queries the same operator (`<=>`)
    # this index accelerates.
    op.execute(
        "CREATE INDEX ix_review_embeddings_cosine ON review_embeddings "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.drop_index("ix_review_embeddings_cosine", table_name="review_embeddings")
    op.drop_table("review_embeddings")
