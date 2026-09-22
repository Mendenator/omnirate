"""Redis-backed review-velocity tracking feeding app/domain/surge.py's
z-score check. 5-minute buckets, 24h (288 bucket) rolling window — enough
history for a meaningful stdev without keeping unbounded state per entity.
"""

from redis.asyncio import Redis

from app.domain.surge import SurgeCheckResult, check_surge

BUCKET_SECONDS = 300
HISTORY_BUCKETS = 288  # 24h of 5-min buckets
BUCKET_TTL_SECONDS = HISTORY_BUCKETS * BUCKET_SECONDS


def _bucket_key(entity_id: str, bucket_index: int) -> str:
    return f"surge:{entity_id}:{bucket_index}"


async def record_review_and_check_surge(redis: Redis, *, entity_id: str, now_epoch: int) -> SurgeCheckResult:
    current_bucket = now_epoch // BUCKET_SECONDS
    current_count = await redis.incr(_bucket_key(entity_id, current_bucket))
    await redis.expire(_bucket_key(entity_id, current_bucket), BUCKET_TTL_SECONDS)

    history_keys = [_bucket_key(entity_id, current_bucket - i) for i in range(1, HISTORY_BUCKETS + 1)]
    raw_history = await redis.mget(history_keys) if history_keys else []
    historical_counts = [int(v) for v in raw_history if v is not None]

    return check_surge(current_count, historical_counts)
