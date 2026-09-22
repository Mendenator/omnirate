from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Review
from app.domain.scoring import ScoredReview, compute_bayesian_trimmed_score

SCORE_CACHE_TTL_SECONDS = 300
CATEGORY_PRIOR_CONFIDENCE = 10.0  # ~10 "phantom" average reviews worth of pull toward the prior


def _redis_key(entity_id: str) -> str:
    return f"entity:{entity_id}:score"


async def materialize_entity_score(
    db: AsyncSession, redis: Redis, *, entity_id: str, category_prior_mean: float
) -> float:
    reviews = (await db.execute(select(Review).where(Review.entity_id == entity_id))).scalars().all()
    scored = [
        ScoredReview(overall_score=float(r.overall_score), poe_level=r.poe_level, fraud_score=float(r.fraud_score))
        for r in reviews
    ]
    score = compute_bayesian_trimmed_score(
        scored, prior_mean=category_prior_mean, prior_confidence=CATEGORY_PRIOR_CONFIDENCE
    )
    await redis.set(_redis_key(entity_id), str(score), ex=SCORE_CACHE_TTL_SECONDS)
    return score


async def get_cached_entity_score(redis: Redis, *, entity_id: str) -> float | None:
    raw = await redis.get(_redis_key(entity_id))
    return float(raw) if raw is not None else None
