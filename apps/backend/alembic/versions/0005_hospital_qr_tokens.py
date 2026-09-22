"""P2-03: hospital_qr_tokens table.

Revision ID: 0005_hospital_qr_tokens
Revises: 0004_location_pings
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0005_hospital_qr_tokens"
down_revision = "0004_location_pings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hospital_qr_tokens",
        sa.Column("jti", sa.String(36), primary_key=True),
        sa.Column("entity_id", UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("hospital_qr_tokens")
