"""Attendance import orchestration (P3-03). Any exception here propagates to
the caller (the arq cron job in app/workers — see docstring) uncaught, which
is deliberate: Sentry (app/core/observability.configure_sentry) is what
turns "an uncaught exception happened in a cron job" into an alert, so this
function shouldn't swallow errors to be "safe."
"""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.attendance_source import fetch_attendance_records
from app.domain.models import Entity, PoliticianAttendance


async def import_attendance(db: AsyncSession, *, source_url: str | None = None) -> dict[str, int]:
    records = await fetch_attendance_records(source_url)

    # external_id -> entity_id mapping lives in entities.attributes (schema-
    # driven, see docs/politician_schema.sample.json), not a dedicated column.
    entities = (await db.execute(select(Entity).where(Entity.category_slug == "uikh-gishuun"))).scalars().all()
    external_id_to_entity: dict[str, str] = {}
    for e in entities:
        external_id = e.attributes.get("politician_external_id")
        if external_id:
            external_id_to_entity[str(external_id)] = str(e.id)

    matched, unmatched = 0, 0
    for record in records:
        entity_id = external_id_to_entity.get(record.politician_external_id)
        if entity_id is None:
            unmatched += 1
            continue

        stmt = insert(PoliticianAttendance).values(
            entity_id=entity_id, period=record.period, attendance_pct=record.attendance_pct, source_url=source_url or ""
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["entity_id", "period"], set_={"attendance_pct": record.attendance_pct}
        )
        await db.execute(stmt)
        matched += 1

    await db.commit()
    return {"matched": matched, "unmatched": unmatched, "total": len(records)}
