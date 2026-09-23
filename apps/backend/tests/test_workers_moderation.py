import uuid

from app.domain.models import Entity, Review, User
from app.workers.moderation import STRICT_DEFAMATION_BRANCH, moderate_review, on_job_failed_permanently


async def _seed_review(db_session, *, branch_slug="hool-zoog", body="Маш сайн үйлчилгээ байсан"):
    user = User(rd_hash=f"rd-{uuid.uuid4()}", display_name="Test User", poe_level="L2")
    entity = Entity(branch_slug=branch_slug, category_slug="restoran", schema_version=1, name="Test Entity")
    db_session.add_all([user, entity])
    await db_session.flush()
    review = Review(entity_id=entity.id, user_id=user.id, poe_level="L2", overall_score=4.0, body=body)
    db_session.add(review)
    await db_session.commit()
    return review


async def test_skips_when_review_already_deleted(db_session, worker_db):
    result = await moderate_review({}, str(uuid.uuid4()))
    assert result == {"status": "skipped", "reason": "review deleted before moderation ran"}


async def test_redacts_pii_from_review_body(db_session, worker_db):
    review = await _seed_review(db_session, body="Утас: 99001122, тавь")

    result = await moderate_review({}, str(review.id))

    assert result["status"] == "ok"
    assert result["pii_findings"] >= 1
    await db_session.refresh(review)
    assert "99001122" not in review.body


async def test_clean_body_is_untouched(db_session, worker_db):
    review = await _seed_review(db_session, body="Маш сайн үйлчилгээ байсан")

    result = await moderate_review({}, str(review.id))

    assert result == {"status": "ok", "pii_findings": 0}


async def test_strict_defamation_blocks_unsourced_allegation_on_political_branch(db_session, worker_db):
    review = await _seed_review(
        db_session, branch_slug=STRICT_DEFAMATION_BRANCH, body="Энэ хүн хулгайлсан гэдэг яриа байна"
    )

    result = await moderate_review({}, str(review.id))

    assert result == {"status": "blocked", "reason": "unsourced_criminal_allegation"}
    await db_session.refresh(review)
    assert review.is_blocked is True
    assert review.blocked_reason == "unsourced_criminal_allegation"


async def test_strict_defamation_does_not_apply_outside_political_branch(db_session, worker_db):
    review = await _seed_review(db_session, branch_slug="hool-zoog", body="Энэ хүн хулгайлсан гэдэг яриа байна")

    result = await moderate_review({}, str(review.id))

    # Non-political branch: not blocked by defamation, but PII-scanned as usual.
    assert result["status"] == "ok"


async def test_sourced_allegation_on_political_branch_is_not_blocked(db_session, worker_db):
    review = await _seed_review(
        db_session,
        branch_slug=STRICT_DEFAMATION_BRANCH,
        body="Энэ хүн хулгайлсан (эх сурвалж: https://example.mn/case/1)",
    )

    result = await moderate_review({}, str(review.id))

    assert result["status"] == "ok"


async def test_on_job_failed_permanently_pushes_to_dlq():
    import fakeredis

    redis = fakeredis.FakeAsyncRedis()
    await on_job_failed_permanently({"redis": redis}, "review-123", "boom")

    dlq_len = await redis.llen("moderation:dlq")
    assert dlq_len == 1
