"""Automated monthly transparency report (P3-07).

Queries Postgres directly rather than the Parquet lake (app/analytics/
export_pipeline.py) — moderation/takedown tables aren't in that pipeline's
EXPORTED_TABLES yet, and a monthly count over these tables is small enough
that OLTP-table scan cost isn't a concern the way P2-07's 100M-row entity
analytics is. If moderation volume ever grows enough to need the columnar
path, extending EXPORTED_TABLES is the change, not this module.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Complaint, Review, TakedownRequest


@dataclass(frozen=True)
class TransparencyReport:
    period: str
    reviews_deleted: int
    reviews_restored: int
    complaints_received: int
    complaints_resolved: int
    takedowns_received: int
    takedowns_resolved: int
    takedowns_rejected: int


async def generate_monthly_report(
    db: AsyncSession, *, period_start: datetime, period_end: datetime
) -> TransparencyReport:
    reviews_deleted = await db.scalar(
        select(func.count())
        .select_from(Review)
        .where(Review.is_blocked.is_(True), Review.created_at >= period_start, Review.created_at < period_end)
    )

    takedowns_received = await db.scalar(
        select(func.count())
        .select_from(TakedownRequest)
        .where(TakedownRequest.created_at >= period_start, TakedownRequest.created_at < period_end)
    )
    takedowns_resolved = await db.scalar(
        select(func.count())
        .select_from(TakedownRequest)
        .where(
            TakedownRequest.status == "resolved",
            TakedownRequest.resolved_at >= period_start,
            TakedownRequest.resolved_at < period_end,
        )
    )
    takedowns_rejected = await db.scalar(
        select(func.count())
        .select_from(TakedownRequest)
        .where(
            TakedownRequest.status == "rejected",
            TakedownRequest.resolved_at >= period_start,
            TakedownRequest.resolved_at < period_end,
        )
    )

    complaints_received = await db.scalar(
        select(func.count())
        .select_from(Complaint)
        .where(Complaint.created_at >= period_start, Complaint.created_at < period_end)
    )
    complaints_resolved = await db.scalar(
        select(func.count())
        .select_from(Complaint)
        .where(Complaint.status == "resolved", Complaint.created_at >= period_start, Complaint.created_at < period_end)
    )

    return TransparencyReport(
        period=f"{period_start:%Y-%m}",
        reviews_deleted=reviews_deleted or 0,
        reviews_restored=takedowns_rejected or 0,  # a rejected takedown = content stayed up / was restored to visible
        complaints_received=complaints_received or 0,
        complaints_resolved=complaints_resolved or 0,
        takedowns_received=takedowns_received or 0,
        takedowns_resolved=takedowns_resolved or 0,
        takedowns_rejected=takedowns_rejected or 0,
    )


def render_markdown(report: TransparencyReport) -> str:
    return f"""# Ил тод байдлын тайлан — {report.period}

| Хэмжүүр | Тоо |
|---|---|
| Устгасан үнэлгээ | {report.reviews_deleted} |
| Сэргээсэн (takedown татгалзсан) | {report.reviews_restored} |
| Хүлээн авсан гомдол | {report.complaints_received} |
| Шийдвэрлэсэн гомдол | {report.complaints_resolved} |
| Хүлээн авсан устгах хүсэлт | {report.takedowns_received} |
| Биелүүлсэн устгах хүсэлт | {report.takedowns_resolved} |
| Татгалзсан устгах хүсэлт | {report.takedowns_rejected} |
"""
