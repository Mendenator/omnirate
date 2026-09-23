import uuid
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
    attributes: dict[str, Any]
    verified: bool

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
