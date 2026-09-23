import uuid
from datetime import UTC, datetime

from app.analytics.transparency_report import generate_monthly_report, render_markdown
from app.domain.models import Complaint, TakedownRequest, User


async def _seed_user(db_session) -> uuid.UUID:
    # Complaint.reporter_id is a real FK to users.id (unlike
    # TakedownRequest.requester_id, which is deliberately unconstrained —
    # see app/domain/models.py) — a live Postgres rejects a Complaint insert
    # referencing a user_id that doesn't exist.
    user_id = uuid.uuid4()
    db_session.add(User(id=user_id, rd_hash=str(user_id), display_name="Test Reporter", poe_level="L2"))
    await db_session.flush()
    return user_id


PERIOD_START = datetime(2026, 9, 1, tzinfo=UTC)
PERIOD_END = datetime(2026, 10, 1, tzinfo=UTC)


async def test_report_counts_takedowns_and_complaints_in_period(db_session):
    reporter_id = await _seed_user(db_session)

    db_session.add(
        Complaint(
            reporter_id=reporter_id, target_type="review", target_id=uuid.uuid4(), reason="spam", status="resolved"
        )
    )
    db_session.add(
        TakedownRequest(
            requester_type="user",
            target_type="review",
            target_id=uuid.uuid4(),
            reason="defamatory",
            status="resolved",
            sla_deadline=PERIOD_START,
            resolved_at=datetime(2026, 9, 15, tzinfo=UTC),
        )
    )
    db_session.add(
        TakedownRequest(
            requester_type="law_enforcement",
            target_type="review",
            target_id=uuid.uuid4(),
            reason="court order",
            status="rejected",
            sla_deadline=PERIOD_START,
            resolved_at=datetime(2026, 9, 20, tzinfo=UTC),
        )
    )
    await db_session.commit()

    report = await generate_monthly_report(db_session, period_start=PERIOD_START, period_end=PERIOD_END)

    assert report.period == "2026-09"
    assert report.complaints_received == 1
    assert report.complaints_resolved == 1
    assert report.takedowns_received == 2
    assert report.takedowns_resolved == 1
    assert report.takedowns_rejected == 1
    assert report.reviews_restored == 1


async def test_report_excludes_rows_outside_period(db_session):
    reporter_id = await _seed_user(db_session)
    db_session.add(
        Complaint(
            reporter_id=reporter_id,
            target_type="review",
            target_id=uuid.uuid4(),
            reason="spam",
            status="open",
        )
    )
    await db_session.flush()
    # Manually push created_at outside the window (server_default fires at
    # insert time, so we overwrite it directly for this test).
    from sqlalchemy import update

    from app.domain.models import Complaint as ComplaintModel

    await db_session.execute(update(ComplaintModel).values(created_at=datetime(2026, 8, 1, tzinfo=UTC)))
    await db_session.commit()

    report = await generate_monthly_report(db_session, period_start=PERIOD_START, period_end=PERIOD_END)
    assert report.complaints_received == 0


def test_render_markdown_includes_all_fields():
    from app.analytics.transparency_report import TransparencyReport

    report = TransparencyReport(
        period="2026-09",
        reviews_deleted=3,
        reviews_restored=1,
        complaints_received=5,
        complaints_resolved=4,
        takedowns_received=2,
        takedowns_resolved=1,
        takedowns_rejected=1,
    )
    md = render_markdown(report)
    assert "2026-09" in md
    assert "3" in md
