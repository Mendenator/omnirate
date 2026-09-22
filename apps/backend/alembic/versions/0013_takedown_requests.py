"""P3-05/P3-06: takedown_requests table.

Revision ID: 0013_takedown_requests
Revises: 0012_review_blocking
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0013_takedown_requests"
down_revision = "0012_review_blocking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "takedown_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("requester_id", UUID(as_uuid=True)),
        sa.Column("requester_type", sa.String(16), nullable=False),
        sa.Column("target_type", sa.String(16), nullable=False),
        sa.Column("target_id", UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(2000), nullable=False),
        sa.Column("case_reference", sa.String(255)),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("sla_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("requester_type IN ('user','law_enforcement')", name="ck_takedown_requester_type"),
        sa.CheckConstraint("target_type IN ('review','entity')", name="ck_takedown_target_type"),
        sa.CheckConstraint("status IN ('open','reviewing','resolved','rejected')", name="ck_takedown_status"),
    )


def downgrade() -> None:
    op.drop_table("takedown_requests")
