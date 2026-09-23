"""P3-07 scheduled report — 1st of each month, covering the prior month."""

from datetime import UTC, datetime
from typing import Any

from arq import cron
from arq.connections import RedisSettings
from dateutil.relativedelta import relativedelta

from app.analytics.transparency_report import generate_monthly_report, render_markdown
from app.core.config import get_settings
from app.db.session import async_session_factory


async def run_monthly_report(ctx: dict[str, Any]) -> None:
    now = datetime.now(UTC)
    period_start = (now.replace(day=1) - relativedelta(months=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    period_end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    async with async_session_factory() as db:
        report = await generate_monthly_report(db, period_start=period_start, period_end=period_end)
        print(render_markdown(report))


class WorkerSettings:
    cron_jobs = [cron(run_monthly_report, day={1}, hour={2}, minute={0})]
    # Must be a plain RedisSettings instance, not a method — see
    # app/workers/indexer.py's WorkerSettings for why.
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
