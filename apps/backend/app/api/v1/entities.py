from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import EntityCreateRequest, EntityDetailResponse, EntityResponse, ReviewListItem
from app.db.session import get_db
from app.domain.models import Entity, Review
from app.domain.poe import counts_as_verified
from app.domain.scoring import ScoredReview, compute_bayesian_trimmed_score, compute_criteria_breakdown

router = APIRouter(prefix="/api/v1/entities", tags=["entities"])

# Matches app/workers/indexer.py's placeholder category prior (S-08's gold
# set will replace both with real per-category values before P1 sign-off).
CATEGORY_PRIOR_MEAN = 3.5
CATEGORY_PRIOR_CONFIDENCE = 10.0


@router.post("", response_model=EntityResponse, status_code=201)
async def create_entity(req: EntityCreateRequest, request: Request, db: AsyncSession = Depends(get_db)) -> Entity:
    entity = Entity(**req.model_dump())
    db.add(entity)
    try:
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=422, detail=f"entity rejected: {exc}") from exc
    await db.refresh(entity)

    # Without this a new entity only reaches search/listings once someone
    # reviews it (reviews.py is the other place that enqueues a reindex).
    arq_pool = getattr(request.app.state, "arq_pool", None)
    if arq_pool is not None:
        await arq_pool.enqueue_job("reindex_entity", str(entity.id))

    return entity


@router.get("/{entity_id}", response_model=EntityDetailResponse)
async def get_entity(entity_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    entity = await db.get(Entity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="entity not found")

    reviews = (
        (await db.execute(select(Review).where(Review.entity_id == entity.id, Review.is_blocked.is_(False))))
        .scalars()
        .all()
    )

    score = compute_bayesian_trimmed_score(
        [
            ScoredReview(overall_score=float(r.overall_score), poe_level=r.poe_level, fraud_score=float(r.fraud_score))
            for r in reviews
        ],
        prior_mean=CATEGORY_PRIOR_MEAN,
        prior_confidence=CATEGORY_PRIOR_CONFIDENCE,
    )

    return {
        **EntityResponse.model_validate(entity).model_dump(),
        "score": score,
        "review_count": len(reviews),
        "verified_review_count": sum(1 for r in reviews if counts_as_verified(r.poe_level)),
        "criteria_breakdown": compute_criteria_breakdown([r.criteria_scores for r in reviews]),
    }


@router.get("/{entity_id}/reviews", response_model=list[ReviewListItem])
async def list_reviews(entity_id: str, db: AsyncSession = Depends(get_db)) -> list[Review]:
    entity = await db.get(Entity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="entity not found")

    result = await db.execute(
        select(Review)
        .where(Review.entity_id == entity_id, Review.is_blocked.is_(False))
        .order_by(Review.created_at.desc())
    )
    return list(result.scalars().all())
