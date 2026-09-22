"""Initial schema: users, schema_registry_entries, entities, reviews, poe_evidence,
idempotency_keys, audit_log — plus a trigger that enforces entities.attributes
against the category's published JSON Schema via pg_jsonschema (P0-04 acceptance:
invalid attributes rejected at DB level).

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-22
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    # pg_jsonschema: https://github.com/supabase/pg_jsonschema — provides
    # jsonschema_is_valid(schema jsonb, instance jsonb) used by the trigger below.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_jsonschema")

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("rd_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("poe_level", sa.String(2), nullable=False, server_default="L0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("poe_level IN ('L0','L1','L2','L3','L4')", name="ck_users_poe_level"),
    )

    op.create_table(
        "schema_registry_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("category_slug", sa.String(128), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("json_schema", JSONB, nullable=False),
        sa.Column("search_config", JSONB, nullable=False, server_default="{}"),
        sa.Column("display_config", JSONB, nullable=False, server_default="{}"),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("category_slug", "version", name="uq_schema_category_version"),
    )

    op.create_table(
        "entities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("branch_slug", sa.String(64), nullable=False),
        sa.Column("category_slug", sa.String(128), nullable=False),
        sa.Column("schema_version", sa.Integer, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location_slug", sa.String(255)),
        sa.Column("lat", sa.Numeric(9, 6)),
        sa.Column("lon", sa.Numeric(9, 6)),
        sa.Column("attributes", JSONB, nullable=False, server_default="{}"),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["category_slug", "schema_version"],
            ["schema_registry_entries.category_slug", "schema_registry_entries.version"],
            name="fk_entities_schema_version",
        ),
    )
    op.create_index("ix_entities_branch_category", "entities", ["branch_slug", "category_slug"])
    op.create_index("ix_entities_location", "entities", ["location_slug"])

    op.create_table(
        "reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_id", UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("poe_level", sa.String(2), nullable=False, server_default="L0"),
        sa.Column("overall_score", sa.Numeric(3, 2), nullable=False),
        sa.Column("criteria_scores", JSONB, nullable=False, server_default="{}"),
        sa.Column("body", sa.String(4000)),
        sa.Column("fraud_score", sa.Numeric(4, 3), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("entity_id", "user_id", name="uq_review_entity_user"),
        sa.CheckConstraint("poe_level IN ('L0','L1','L2','L3','L4')", name="ck_reviews_poe_level"),
        sa.CheckConstraint("overall_score >= 0 AND overall_score <= 5", name="ck_reviews_score_range"),
    )

    op.create_table(
        "poe_evidence",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("review_id", UUID(as_uuid=True), sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("payload", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("kind IN ('e_barimt','gps','ocr_receipt')", name="ck_poe_evidence_kind"),
    )

    op.create_table(
        "idempotency_keys",
        sa.Column("key", sa.String(255), primary_key=True),
        sa.Column("route", sa.String(255), primary_key=True),
        sa.Column("response_status", sa.Integer, nullable=False),
        sa.Column("response_body", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", UUID(as_uuid=True)),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("target_type", sa.String(64), nullable=False),
        sa.Column("target_id", sa.String(255), nullable=False),
        sa.Column("payload", JSONB, nullable=False, server_default="{}"),
        sa.Column("prev_hash", sa.String(64)),
        sa.Column("row_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- DB-level attribute validation (P0-04 acceptance criterion) ---------
    # A true CHECK constraint can't join to schema_registry_entries, so we use
    # a BEFORE INSERT/UPDATE trigger that raises (and thus rejects the write)
    # when `attributes` doesn't satisfy the category's published JSON Schema.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_entity_attributes_schema() RETURNS trigger AS $$
        DECLARE
            schema_doc jsonb;
        BEGIN
            SELECT json_schema INTO schema_doc
            FROM schema_registry_entries
            WHERE category_slug = NEW.category_slug AND version = NEW.schema_version;

            IF schema_doc IS NULL THEN
                RAISE EXCEPTION 'no published schema for category=% version=%',
                    NEW.category_slug, NEW.schema_version;
            END IF;

            IF NOT jsonschema_is_valid(schema_doc, NEW.attributes) THEN
                RAISE EXCEPTION 'entity.attributes failed schema validation for category=%',
                    NEW.category_slug;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_entities_validate_attributes
        BEFORE INSERT OR UPDATE OF attributes ON entities
        FOR EACH ROW EXECUTE FUNCTION enforce_entity_attributes_schema();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_entities_validate_attributes ON entities")
    op.execute("DROP FUNCTION IF EXISTS enforce_entity_attributes_schema")
    op.drop_table("audit_log")
    op.drop_table("idempotency_keys")
    op.drop_table("poe_evidence")
    op.drop_table("reviews")
    op.drop_index("ix_entities_location", table_name="entities")
    op.drop_index("ix_entities_branch_category", table_name="entities")
    op.drop_table("entities")
    op.drop_table("schema_registry_entries")
    op.drop_table("users")
