import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EntityCreateRequest(BaseModel):
    branch_slug: str
    category_slug: str
    schema_version: int
    name: str
    ttd: str | None = None
    location_slug: str | None = None
    lat: float | None = None
    lon: float | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class EntityResponse(BaseModel):
    id: uuid.UUID
    branch_slug: str
    category_slug: str
    schema_version: int
    name: str
    ttd: str | None
    location_slug: str | None
    lat: float | None
    lon: float | None
    attributes: dict[str, Any]
    verified: bool

    model_config = {"from_attributes": True}


class EntityDetailResponse(EntityResponse):
    """GET /entities/{id}: EntityResponse plus what the entity page's
    summary/criteria_breakdown sections need, computed live from the
    entity's non-blocked reviews (P1-10)."""

    score: float
    review_count: int
    verified_review_count: int
    criteria_breakdown: dict[str, float]


class ReviewListItem(BaseModel):
    """Public-facing review shape for GET /entities/{id}/reviews — omits
    user_id (no reviewer identity beyond poe_level is shown publicly)."""

    id: uuid.UUID
    poe_level: str
    overall_score: float
    criteria_scores: dict[str, float]
    body: str | None
    owner_reply_body: str | None
    owner_reply_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewCreateRequest(BaseModel):
    entity_id: uuid.UUID
    overall_score: float = Field(ge=0, le=5)
    criteria_scores: dict[str, float] = Field(default_factory=dict)
    body: str | None = Field(default=None, max_length=4000)


class ReviewResponse(BaseModel):
    id: uuid.UUID
    entity_id: uuid.UUID
    user_id: uuid.UUID
    poe_level: str
    overall_score: float
    criteria_scores: dict[str, float]
    body: str | None

    model_config = {"from_attributes": True}
