"""P3-03: politician_attendance table.

Revision ID: 0011_politician_attendance
Revises: 0010_district_mappings
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "0011_politician_attendance"
down_revision = "0010_district_mappings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "politician_attendance",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_id", UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period", sa.String(16), nullable=False),
        sa.Column("attendance_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("source_url", sa.String(512), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("entity_id", "period", name="uq_politician_attendance_entity_period"),
    )


def downgrade() -> None:
    op.drop_table("politician_attendance")
