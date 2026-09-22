"""Core domain schema (P0-04): 6 tables + audit_log.

1. users                    — ДАН-verified accounts (РД stored as HMAC hash only)
2. schema_registry_entries  — versioned, immutable-once-published category schemas
3. entities                 — rated things (restaurant, hospital, politician, ...)
4. reviews                  — PoE-backed ratings, 1-per-(user, entity) via unique idx
5. poe_evidence             — e-barimt / GPS / OCR evidence backing a review's PoE level
6. idempotency_keys          — request idempotency ledger for POST /reviews etc.
7. audit_log                — append-only, hash-chained action log
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

POE_LEVELS = ("L0", "L1", "L2", "L3", "L4")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rd_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    poe_level: Mapped[str] = mapped_column(String(2), nullable=False, default="L0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (CheckConstraint(f"poe_level IN {POE_LEVELS}", name="ck_users_poe_level"),)


class SchemaRegistryEntry(Base):
    __tablename__ = "schema_registry_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_slug: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    json_schema: Mapped[dict] = mapped_column(JSONB, nullable=False)
    search_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    display_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("category_slug", "version", name="uq_schema_category_version"),
    )


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    branch_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    category_slug: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_slug: Mapped[str | None] = mapped_column(String(255))
    lat: Mapped[float | None] = mapped_column(Numeric(9, 6))
    lon: Mapped[float | None] = mapped_column(Numeric(9, 6))
    attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    verified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    reviews: Mapped[list["Review"]] = relationship(back_populates="entity")

    __table_args__ = (
        Index("ix_entities_branch_category", "branch_slug", "category_slug"),
        Index("ix_entities_location", "location_slug"),
    )


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    poe_level: Mapped[str] = mapped_column(String(2), nullable=False, default="L0")
    overall_score: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    criteria_scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    body: Mapped[str | None] = mapped_column(String(4000))
    fraud_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    entity: Mapped[Entity] = relationship(back_populates="reviews")

    __table_args__ = (
        # One review per user per entity — duplicate submission -> 409 (P0-06 acceptance).
        UniqueConstraint("entity_id", "user_id", name="uq_review_entity_user"),
        CheckConstraint(f"poe_level IN {POE_LEVELS}", name="ck_reviews_poe_level"),
        CheckConstraint("overall_score >= 0 AND overall_score <= 5", name="ck_reviews_score_range"),
    )


class PoeEvidence(Base):
    __tablename__ = "poe_evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)  # e_barimt | gps | ocr_receipt
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("kind IN ('e_barimt', 'gps', 'ocr_receipt')", name="ck_poe_evidence_kind"),
    )


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    route: Mapped[str] = mapped_column(String(255), primary_key=True)
    response_status: Mapped[int] = mapped_column(nullable=False)
    response_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    prev_hash: Mapped[str | None] = mapped_column(String(64))
    row_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
