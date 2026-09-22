"""P2-07: analytics_export_state watermark table.

Revision ID: 0006_analytics_export_state
Revises: 0005_hospital_qr_tokens
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from alembic import op

revision = "0006_analytics_export_state"
down_revision = "0005_hospital_qr_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analytics_export_state",
        sa.Column("table_name", sa.String(64), primary_key=True),
        sa.Column("watermark", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("analytics_export_state")
