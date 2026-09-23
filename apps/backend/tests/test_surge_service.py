import fakeredis

from app.domain.surge_service import record_review_and_check_surge


async def test_first_review_never_flags_surge():
    redis = fakeredis.FakeAsyncRedis()
    result = await record_review_and_check_surge(redis, entity_id="entity-1", now_epoch=1_700_000_000)
    assert result.is_surge is False


async def test_repeated_calls_in_the_same_bucket_stay_quiet_without_history():
    redis = fakeredis.FakeAsyncRedis()
    now = 1_700_000_000
    result = None
    for _ in range(5):
        result = await record_review_and_check_surge(redis, entity_id="entity-2", now_epoch=now)
    # No history yet (MIN_HISTORY_BUCKETS_FOR_SIGNAL not met) -> never flags,
    # regardless of how many reviews land in the current bucket.
    assert result.is_surge is False
    assert result.z_score == 0.0


async def test_different_entities_track_independent_buckets():
    redis = fakeredis.FakeAsyncRedis()
    now = 1_700_000_000
    await record_review_and_check_surge(redis, entity_id="entity-a", now_epoch=now)
    result_b = await record_review_and_check_surge(redis, entity_id="entity-b", now_epoch=now)
    # entity-b's bucket is independent of entity-a's — still below the
    # history threshold, so it reads as quiet rather than inheriting entity-a's state.
    assert result_b.is_surge is False


async def test_sudden_spike_against_quiet_history_flags_surge():
    redis = fakeredis.FakeAsyncRedis()
    bucket_seconds = 300
    base = 1_700_000_000

    # Establish a quiet history: 1 review/bucket for a while.
    for i in range(1, 20):
        await record_review_and_check_surge(redis, entity_id="entity-3", now_epoch=base - i * bucket_seconds)

    # Now a burst of reviews all landing in the current bucket.
    result = None
    for _ in range(30):
        result = await record_review_and_check_surge(redis, entity_id="entity-3", now_epoch=base)

    assert result.is_surge is True
