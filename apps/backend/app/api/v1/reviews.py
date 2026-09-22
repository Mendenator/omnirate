from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.idempotency import get_cached_response, store_response
from app.api.v1.schemas import ReviewCreateRequest, ReviewResponse
from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.domain.models import Review

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

_ROUTE = "POST /api/v1/reviews"


@router.post("", response_model=ReviewResponse, status_code=201)
async def create_review(
    req: ReviewCreateRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    cached = await get_cached_response(db, key=idempotency_key, route=_ROUTE)
    if cached is not None:
        status, body = cached
        if status >= 400:
            raise HTTPException(status_code=status, detail=body)
        return body

    review = Review(
        entity_id=req.entity_id,
        user_id=user.user_id,
        poe_level=user.poe_level,
        overall_score=req.overall_score,
        criteria_scores=req.criteria_scores,
        body=req.body,
    )
    db.add(review)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        # One review per (entity, user) — duplicate submission is a 409, not a 500.
        body = {"detail": "review already exists for this user and entity"}
        await store_response(db, key=idempotency_key, route=_ROUTE, status=409, body=body)
        raise HTTPException(status_code=409, detail=body["detail"]) from exc

    await db.refresh(review)
    response = ReviewResponse.model_validate(review).model_dump(mode="json")
    await store_response(db, key=idempotency_key, route=_ROUTE, status=201, body=response)

    arq_pool = getattr(request.app.state, "arq_pool", None)
    if arq_pool is not None:
        await arq_pool.enqueue_job("moderate_review", str(review.id), _queue_name="arq:queue:moderation")

    return review
