"""P1-13/P1-14: entity_owners, complaints, reviews.owner_reply_*.

Revision ID: 0003_owner_claims_complaints
Revises: 0002_e_barimt_receipts
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "0003_owner_claims_complaints"
down_revision = "0002_e_barimt_receipts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("owner_reply_body", sa.String(2000)))
    op.add_column("reviews", sa.Column("owner_reply_at", sa.DateTime(timezone=True)))

    op.create_table(
        "entity_owners",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_id", UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("entity_id", name="uq_entity_owners_entity"),
    )

    op.create_table(
        "complaints",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("reporter_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("details", sa.String(2000)),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("target_type IN ('review', 'entity')", name="ck_complaints_target_type"),
        sa.CheckConstraint("status IN ('open', 'reviewing', 'resolved', 'dismissed')", name="ck_complaints_status"),
    )


def downgrade() -> None:
    op.drop_table("complaints")
    op.drop_table("entity_owners")
    op.drop_column("reviews", "owner_reply_at")
    op.drop_column("reviews", "owner_reply_body")
