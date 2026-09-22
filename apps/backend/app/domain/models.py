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
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.ml.embeddings import EMBEDDING_DIM

POE_LEVELS = ("L0", "L1", "L2", "L3", "L4")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rd_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    poe_level: Mapped[str] = mapped_column(String(2), nullable=False, default="L0")
    khoroo_slug: Mapped[str | None] = mapped_column(String(64))  # registered address, for P3-02 jurisdiction_match
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
    ttd: Mapped[str | None] = mapped_column(String(32))  # taxpayer registration no., for e-barimt TTD match (P1-01)
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
    owner_reply_body: Mapped[str | None] = mapped_column(String(2000))
    owner_reply_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_blocked: Mapped[bool] = mapped_column(nullable=False, default=False)  # P3-04: strict_defamation, etc.
    blocked_reason: Mapped[str | None] = mapped_column(String(64))
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


class EBarimtReceipt(Base):
    """P1-01: one row per verified e-barimt receipt. `ddtd` UNIQUE enforces
    "ДДТД UNIQUE" (a receipt can back exactly one review, no replay)."""

    __tablename__ = "e_barimt_receipts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    ddtd: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    ttd: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EntityOwner(Base):
    """P1-13: an owner claim is only inserted once the submitted TTD matches
    the entity's registered TTD — mismatches are rejected in the API layer
    before a row is ever written (acceptance: 100% of TTD-mismatched claims
    rejected)."""

    __tablename__ = "entity_owners"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("entity_id", name="uq_entity_owners_entity"),)


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)  # review | entity
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[str | None] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("target_type IN ('review', 'entity')", name="ck_complaints_target_type"),
        CheckConstraint("status IN ('open', 'reviewing', 'resolved', 'dismissed')", name="ck_complaints_status"),
    )


class LocationPing(Base):
    """P2-01: raw GPS pings backing a review's dwell-time evidence. Kept even
    after the PoE decision is made — the pattern-of-life across pings is what
    surge-mode/red-team analysis (P2-14) audits after the fact."""

    __tablename__ = "location_pings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    lat: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    lon: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    accuracy_m: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    is_mock_provider_flag: Mapped[bool] = mapped_column(nullable=False, default=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_location_pings_review", "review_id"),)


class HospitalQrToken(Base):
    """P2-03: one row per issued QR. `jti` UNIQUE + `used_at` gives the
    "давхар jti 100% татгалзагдах" acceptance a DB-level guarantee, not just
    an application check — a race between two verify requests for the same
    QR still can't both succeed (a second UPDATE ... WHERE used_at IS NULL
    affects 0 rows)."""

    __tablename__ = "hospital_qr_tokens"

    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ReviewEmbedding(Base):
    """P2-10: e5 embedding per review, for pgvector cosine-similarity search
    (near-duplicate/paraphrase clustering — a fraud ring that varies wording
    slightly per review evades exact-text matching but not this)."""

    __tablename__ = "review_embeddings"

    review_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), primary_key=True
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserDevice(Base):
    """P2-13: one row per (user, device) pairing ever seen. `first_seen_at`
    anchors the 7-day cooldown; `last_lat`/`last_lon`/`last_seen_at` feed
    impossible-travel checks across sessions, not just within one GPS trail."""

    __tablename__ = "user_devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_lat: Mapped[float | None] = mapped_column(Numeric(9, 6))
    last_lon: Mapped[float | None] = mapped_column(Numeric(9, 6))

    __table_args__ = (UniqueConstraint("user_id", "device_id", name="uq_user_devices_user_device"),)


class ModerationCase(Base):
    """P2-12: one row per review routed to human moderation (from
    app/ml/llm_moderation.py's "needs_human_review" verdict)."""

    __tablename__ = "moderation_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="awaiting_first_decision")
    final_verdict: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "state IN ('awaiting_first_decision','awaiting_second_decision','resolved','escalated')",
            name="ck_moderation_cases_state",
        ),
    )


class ModerationDecision(Base):
    __tablename__ = "moderation_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("moderation_cases.id", ondelete="CASCADE"), nullable=False)
    moderator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    verdict: Mapped[str] = mapped_column(String(16), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("case_id", "moderator_id", name="uq_moderation_decisions_case_moderator"),
        CheckConstraint("verdict IN ('approve','reject')", name="ck_moderation_decisions_verdict"),
    )


class DistrictMapping(Base):
    """P3-01: хороо -> тойрог, versioned like schema_registry_entries — a new
    version is a new set of rows, never an in-place update of an existing one."""

    __tablename__ = "district_mappings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    khoroo_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    tovrog_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("khoroo_slug", "version", name="uq_district_mappings_khoroo_version"),)


class PoliticianAttendance(Base):
    """P3-03: objective, externally-sourced attendance data — deliberately
    separate from `entities.attributes` (which is self-reported/admin-edited)
    so a moderation dispute over a review can never touch this table, and
    vice versa: a bad import can't corrupt entity attributes."""

    __tablename__ = "politician_attendance"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    period: Mapped[str] = mapped_column(String(16), nullable=False)  # e.g. "2026-Q3"
    attendance_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    source_url: Mapped[str] = mapped_column(String(512), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("entity_id", "period", name="uq_politician_attendance_entity_period"),)


class TakedownRequest(Base):
    """P3-05/P3-06: notice-and-takedown, both user and law-enforcement
    requesters share this table — see app/domain/takedown.py for why."""

    __tablename__ = "takedown_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    requester_type: Mapped[str] = mapped_column(String(16), nullable=False)
    target_type: Mapped[str] = mapped_column(String(16), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    case_reference: Mapped[str | None] = mapped_column(String(255))  # law-enforcement case/badge number
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    sla_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("requester_type IN ('user','law_enforcement')", name="ck_takedown_requester_type"),
        CheckConstraint("target_type IN ('review','entity')", name="ck_takedown_target_type"),
        CheckConstraint("status IN ('open','reviewing','resolved','rejected')", name="ck_takedown_status"),
    )


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
