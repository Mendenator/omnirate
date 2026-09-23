import uuid
from unittest.mock import patch

from app.core.attendance_source import AttendanceRecord
from app.domain.attendance_import import import_attendance
from app.domain.models import Entity, PoliticianAttendance


async def _seed_entity(db_session, external_id: str) -> str:
    entity = Entity(
        id=uuid.uuid4(),
        branch_slug="tur-alba",
        category_slug="uikh-gishuun",
        schema_version=1,
        name="Тест гишүүн",
        attributes={"politician_external_id": external_id},
    )
    db_session.add(entity)
    await db_session.flush()
    return str(entity.id)


async def test_import_matches_records_to_entities_by_external_id(db_session):
    entity_id = await _seed_entity(db_session, "ext-123")
    await db_session.commit()

    records = [AttendanceRecord(politician_external_id="ext-123", period="2026-Q3", attendance_pct=87.5)]
    with patch("app.domain.attendance_import.fetch_attendance_records", return_value=records):
        result = await import_attendance(db_session, source_url="http://example.test")

    assert result == {"matched": 1, "unmatched": 0, "total": 1}

    from sqlalchemy import select

    row = (
        await db_session.execute(select(PoliticianAttendance).where(PoliticianAttendance.entity_id == entity_id))
    ).scalar_one()
    assert float(row.attendance_pct) == 87.5


async def test_import_counts_unmatched_records():
    records = [AttendanceRecord(politician_external_id="unknown-id", period="2026-Q3", attendance_pct=50.0)]
    from app.db.session import async_session_factory

    async with async_session_factory() as db:
        with patch("app.domain.attendance_import.fetch_attendance_records", return_value=records):
            result = await import_attendance(db, source_url="http://example.test")

    assert result["unmatched"] == 1
    assert result["matched"] == 0


async def test_reimport_same_period_updates_rather_than_duplicates(db_session):
    entity_id = await _seed_entity(db_session, "ext-456")
    await db_session.commit()

    first = [AttendanceRecord(politician_external_id="ext-456", period="2026-Q3", attendance_pct=70.0)]
    with patch("app.domain.attendance_import.fetch_attendance_records", return_value=first):
        await import_attendance(db_session, source_url="http://example.test")

    second = [AttendanceRecord(politician_external_id="ext-456", period="2026-Q3", attendance_pct=95.0)]
    with patch("app.domain.attendance_import.fetch_attendance_records", return_value=second):
        await import_attendance(db_session, source_url="http://example.test")

    from sqlalchemy import select

    rows = (
        (await db_session.execute(select(PoliticianAttendance).where(PoliticianAttendance.entity_id == entity_id)))
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert float(rows[0].attendance_pct) == 95.0
