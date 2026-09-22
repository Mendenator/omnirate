"""P2-12: moderation_cases, moderation_decisions.

Revision ID: 0009_moderation_queue
Revises: 0008_user_devices
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0009_moderation_queue"
down_revision = "0008_user_devices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "moderation_cases",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("review_id", UUID(as_uuid=True), sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state", sa.String(32), nullable=False, server_default="awaiting_first_decision"),
        sa.Column("final_verdict", sa.String(16)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "state IN ('awaiting_first_decision','awaiting_second_decision','resolved','escalated')",
            name="ck_moderation_cases_state",
        ),
    )

    op.create_table(
        "moderation_decisions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", UUID(as_uuid=True), sa.ForeignKey("moderation_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("moderator_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("verdict", sa.String(16), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("case_id", "moderator_id", name="uq_moderation_decisions_case_moderator"),
        sa.CheckConstraint("verdict IN ('approve','reject')", name="ck_moderation_decisions_verdict"),
    )


def downgrade() -> None:
    op.drop_table("moderation_decisions")
    op.drop_table("moderation_cases")
