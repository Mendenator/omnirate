"""Entity owner claim + reply (P1-13)."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.domain.models import Entity, EntityOwner, Review

router = APIRouter(prefix="/api/v1/entities", tags=["ownership"])


class ClaimRequest(BaseModel):
    ttd: str


class OwnerReplyRequest(BaseModel):
    body: str


@router.post("/{entity_id}/claim", status_code=201)
async def claim_entity(
    entity_id: str,
    req: ClaimRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    entity = await db.get(Entity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="entity not found")

    # Acceptance: 100% of TTD-mismatched claims rejected before a row exists.
    if entity.ttd is None or req.ttd != entity.ttd:
        raise HTTPException(
            status_code=422, detail={"reason_code": "ttd_mismatch", "message": "TTD does not match entity"}
        )

    owner = EntityOwner(entity_id=entity.id, user_id=user.user_id)
    db.add(owner)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="entity already claimed") from exc

    return {"status": "claimed", "entity_id": str(entity.id)}


async def _assert_is_owner(db: AsyncSession, *, entity_id, user_id) -> None:
    owner = await db.scalar(
        select(EntityOwner).where(EntityOwner.entity_id == entity_id, EntityOwner.user_id == user_id)
    )
    if owner is None:
        raise HTTPException(status_code=403, detail="not the verified owner of this entity")


@router.post("/{entity_id}/reviews/{review_id}/reply", status_code=200)
async def reply_to_review(
    entity_id: str,
    review_id: str,
    req: OwnerReplyRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    await _assert_is_owner(db, entity_id=entity_id, user_id=user.user_id)

    review = await db.get(Review, review_id)
    if review is None or str(review.entity_id) != entity_id:
        raise HTTPException(status_code=404, detail="review not found for this entity")

    review.owner_reply_body = req.body
    review.owner_reply_at = datetime.now(UTC)
    await db.commit()
    return {"status": "replied"}
