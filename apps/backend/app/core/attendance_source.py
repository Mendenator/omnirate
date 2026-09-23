"""Attendance/objective-data source client (P3-03).

⛔ EXTERNAL DEPENDENCY: SOW §6 lists this task's own dependency as "Өгөгдлийн
эх сурвалж" (a data source) — no specific government open-data API has been
named yet, unlike ДАН/e-barimt where the target system is at least known.
Until one is identified, this points at a local mock so the import pipeline
(parsing, upsert, alerting) is built and tested end-to-end.
"""

from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass(frozen=True)
class AttendanceRecord:
    politician_external_id: str  # source system's own ID — mapped to entity_id by the caller
    period: str
    attendance_pct: float


async def fetch_attendance_records(source_url: str | None = None) -> list[AttendanceRecord]:
    settings = get_settings()
    url = source_url or settings.attendance_source_url
    if not url:
        raise NotImplementedError("No attendance data source configured — see docs/PROGRESS.md P3-03")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        body = resp.json()

    return [
        AttendanceRecord(
            politician_external_id=row["politician_id"],
            period=row["period"],
            attendance_pct=float(row["attendance_pct"]),
        )
        for row in body["records"]
    ]
