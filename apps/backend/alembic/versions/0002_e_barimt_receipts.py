"""P1-01: e_barimt_receipts table (ddtd UNIQUE) + entities.ttd for TTD matching.

Revision ID: 0002_e_barimt_receipts
Revises: 0001_initial_schema
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "0002_e_barimt_receipts"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("entities", sa.Column("ttd", sa.String(32)))

    op.create_table(
        "e_barimt_receipts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("review_id", UUID(as_uuid=True), sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ddtd", sa.String(64), nullable=False, unique=True),
        sa.Column("ttd", sa.String(32), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("purchased_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("e_barimt_receipts")
    op.drop_column("entities", "ttd")
