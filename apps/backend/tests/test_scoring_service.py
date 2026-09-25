import uuid

import fakeredis

from app.domain.models import Entity, Review, User
from app.domain.scoring_service import get_cached_entity_score, materialize_entity_score


async def _seed_entity_with_reviews(db_session, *, scores: list[float]) -> str:
    entity = Entity(branch_slug="hool-zoog", category_slug="restoran", schema_version=1, name="Test Entity")
    db_session.add(entity)
    await db_session.flush()

    for i, score in enumerate(scores):
        user = User(rd_hash=f"rd-{uuid.uuid4()}", display_name=f"User {i}", poe_level="L2")
        db_session.add(user)
        await db_session.flush()
        db_session.add(
            Review(entity_id=entity.id, user_id=user.id, poe_level="L2", overall_score=score, fraud_score=0.0)
        )
    await db_session.commit()
    return str(entity.id)


async def test_materialize_entity_score_caches_in_redis(db_session):
    entity_id = await _seed_entity_with_reviews(db_session, scores=[4.5, 5.0, 4.0])
    redis = fakeredis.FakeAsyncRedis()

    score = await materialize_entity_score(db_session, redis, entity_id=entity_id, category_prior_mean=3.5)

    assert 0 <= score <= 5
    cached = await get_cached_entity_score(redis, entity_id=entity_id)
    assert cached == score


async def test_cached_score_is_none_before_materialization():
    redis = fakeredis.FakeAsyncRedis()
    cached = await get_cached_entity_score(redis, entity_id=str(uuid.uuid4()))
    assert cached is None


async def test_no_reviews_falls_back_toward_prior(db_session):
    entity = Entity(branch_slug="hool-zoog", category_slug="restoran", schema_version=1, name="No Reviews Entity")
    db_session.add(entity)
    await db_session.commit()
    redis = fakeredis.FakeAsyncRedis()

    score = await materialize_entity_score(db_session, redis, entity_id=str(entity.id), category_prior_mean=3.5)

    assert score == 3.5


async def test_blocked_reviews_are_excluded_from_the_score(db_session):
    entity = Entity(branch_slug="hool-zoog", category_slug="restoran", schema_version=1, name="Test Entity")
    db_session.add(entity)
    await db_session.flush()
    user = User(rd_hash=f"rd-{uuid.uuid4()}", display_name="Blocked reviewer", poe_level="L4")
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        Review(
            entity_id=entity.id, user_id=user.id, poe_level="L4", overall_score=0.5, fraud_score=0.0, is_blocked=True
        )
    )
    await db_session.commit()
    redis = fakeredis.FakeAsyncRedis()

    score = await materialize_entity_score(db_session, redis, entity_id=str(entity.id), category_prior_mean=3.5)

    assert score == 3.5  # blocked review excluded entirely -> falls back to the prior, unaffected by its 0.5
