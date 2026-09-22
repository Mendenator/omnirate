"""P3-01: district_mappings table + users.khoroo_slug.

Revision ID: 0010_district_mappings
Revises: 0009_moderation_queue
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0010_district_mappings"
down_revision = "0009_moderation_queue"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("khoroo_slug", sa.String(64)))

    op.create_table(
        "district_mappings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("khoroo_slug", sa.String(64), nullable=False),
        sa.Column("tovrog_slug", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("khoroo_slug", "version", name="uq_district_mappings_khoroo_version"),
    )


def downgrade() -> None:
    op.drop_table("district_mappings")
    op.drop_column("users", "khoroo_slug")
