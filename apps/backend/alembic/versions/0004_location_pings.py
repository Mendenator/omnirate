"""P2-01: location_pings table.

Revision ID: 0004_location_pings
Revises: 0003_owner_claims_complaints
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0004_location_pings"
down_revision = "0003_owner_claims_complaints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "location_pings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("review_id", UUID(as_uuid=True), sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lat", sa.Numeric(9, 6), nullable=False),
        sa.Column("lon", sa.Numeric(9, 6), nullable=False),
        sa.Column("accuracy_m", sa.Numeric(6, 2), nullable=False),
        sa.Column("is_mock_provider_flag", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_location_pings_review", "location_pings", ["review_id"])


def downgrade() -> None:
    op.drop_index("ix_location_pings_review", table_name="location_pings")
    op.drop_table("location_pings")
