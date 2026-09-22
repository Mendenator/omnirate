async def test_audit_chain_links_and_verifies(db_session):
    from app.domain.audit import append_audit_log, verify_chain

    e1 = await append_audit_log(
        db_session, actor_id=None, action="review.create", target_type="review", target_id="r1", payload={"x": 1}
    )
    await db_session.flush()
    e2 = await append_audit_log(
        db_session, actor_id=None, action="review.moderate", target_type="review", target_id="r1", payload={"x": 2}
    )
    await db_session.flush()

    assert e2.prev_hash == e1.row_hash
    assert verify_chain([e1, e2]) is True


async def test_audit_chain_detects_tampering(db_session):
    from app.domain.audit import append_audit_log, verify_chain

    e1 = await append_audit_log(
        db_session, actor_id=None, action="review.create", target_type="review", target_id="r1", payload={"x": 1}
    )
    await db_session.flush()
    e2 = await append_audit_log(
        db_session, actor_id=None, action="review.moderate", target_type="review", target_id="r1", payload={"x": 2}
    )
    await db_session.flush()

    e1.payload = {"x": 999}  # tamper with history
    assert verify_chain([e1, e2]) is False
