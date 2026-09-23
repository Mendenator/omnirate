"""P3-04: reviews.is_blocked / blocked_reason.

Revision ID: 0012_review_blocking
Revises: 0011_politician_attendance
Create Date: 2026-09-22
"""

import sqlalchemy as sa

from alembic import op

revision = "0012_review_blocking"
down_revision = "0011_politician_attendance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("is_blocked", sa.Boolean, nullable=False, server_default=sa.false()))
    op.add_column("reviews", sa.Column("blocked_reason", sa.String(64)))


def downgrade() -> None:
    op.drop_column("reviews", "blocked_reason")
    op.drop_column("reviews", "is_blocked")
