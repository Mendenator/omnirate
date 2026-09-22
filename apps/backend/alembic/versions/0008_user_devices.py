"""P2-13: user_devices table.

Revision ID: 0008_user_devices
Revises: 0007_review_embeddings
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0008_user_devices"
down_revision = "0007_review_embeddings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_devices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.String(255), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_lat", sa.Numeric(9, 6)),
        sa.Column("last_lon", sa.Numeric(9, 6)),
        sa.UniqueConstraint("user_id", "device_id", name="uq_user_devices_user_device"),
    )


def downgrade() -> None:
    op.drop_table("user_devices")
