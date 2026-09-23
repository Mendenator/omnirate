import uuid

from app.core.deps import CurrentUser, get_current_user
from app.domain.models import Entity, ModerationCase, Review, User
from app.main import app


async def _seed_case(db_session, *, state="awaiting_first_decision"):
    entity = Entity(branch_slug="hool-zoog", category_slug="restoran", schema_version=1, name="Test Entity")
    user = User(rd_hash=f"rd-{uuid.uuid4()}", display_name="Reviewer", poe_level="L2")
    db_session.add_all([entity, user])
    await db_session.flush()
    review = Review(entity_id=entity.id, user_id=user.id, poe_level="L2", overall_score=1.0, body="new шинэ")
    db_session.add(review)
    await db_session.flush()
    case = ModerationCase(review_id=review.id, state=state)
    db_session.add(case)
    await db_session.commit()
    return case


async def test_queue_lists_only_open_cases(client, db_session):
    open_case = await _seed_case(db_session, state="awaiting_first_decision")
    await _seed_case(db_session, state="resolved")

    resp = await client.get("/api/v1/moderation/queue")

    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert str(open_case.id) in ids
    assert len(ids) == 1


async def test_decide_unknown_case_is_404(client):
    resp = await client.post(f"/api/v1/moderation/cases/{uuid.uuid4()}/decide", json={"verdict": "approve"})
    assert resp.status_code == 404


async def test_decide_already_resolved_case_is_409(client, db_session):
    case = await _seed_case(db_session, state="resolved")
    resp = await client.post(f"/api/v1/moderation/cases/{case.id}/decide", json={"verdict": "approve"})
    assert resp.status_code == 409


async def test_first_decision_moves_case_to_awaiting_second(client, db_session):
    case = await _seed_case(db_session)
    resp = await client.post(f"/api/v1/moderation/cases/{case.id}/decide", json={"verdict": "approve"})
    assert resp.status_code == 200
    assert resp.json()["state"] == "awaiting_second_decision"


async def test_two_agreeing_decisions_resolve_the_case(client, db_session):
    case = await _seed_case(db_session)

    first_user = client.fake_user
    resp1 = await client.post(f"/api/v1/moderation/cases/{case.id}/decide", json={"verdict": "reject"})
    assert resp1.status_code == 200

    second_user = CurrentUser(user_id=uuid.uuid4(), rd_hash="second-mod", poe_level="L2")
    db_session.add(User(id=second_user.user_id, rd_hash="second-mod", display_name="Mod 2", poe_level="L2"))
    await db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: second_user
    try:
        resp2 = await client.post(f"/api/v1/moderation/cases/{case.id}/decide", json={"verdict": "reject"})
    finally:
        app.dependency_overrides[get_current_user] = lambda: first_user

    assert resp2.status_code == 200
    assert resp2.json()["state"] == "resolved"


async def test_same_moderator_deciding_twice_is_409(client, db_session):
    case = await _seed_case(db_session)
    first = await client.post(f"/api/v1/moderation/cases/{case.id}/decide", json={"verdict": "approve"})
    assert first.status_code == 200
    second = await client.post(f"/api/v1/moderation/cases/{case.id}/decide", json={"verdict": "reject"})
    assert second.status_code == 409
