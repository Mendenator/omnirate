"""entities.created_by: who added the entity (POST /entities now needs a login).

Revision ID: 0014_entity_created_by
Revises: 0013_takedown_requests
Create Date: 2026-09-27
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "0014_entity_created_by"
down_revision = "0013_takedown_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "entities",
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("entities", "created_by")
