"""P3-03 scheduled import — daily, per acceptance ("Өдөр бүр шинэчлэгдэх, алдаа
alert-тэй"). An unhandled exception from import_attendance reaches Sentry via
app/core/observability.configure_sentry (called at worker startup).
"""

from typing import Any

from arq import cron
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.observability import configure_sentry
from app.db.session import async_session_factory
from app.domain.attendance_import import import_attendance


async def run_daily_import(ctx: dict[str, Any]) -> None:
    async with async_session_factory() as db:
        result = await import_attendance(db)
        print(f"[attendance-import] {result}")


async def startup(ctx: dict[str, Any]) -> None:
    configure_sentry()


class WorkerSettings:
    cron_jobs = [cron(run_daily_import, hour={3}, minute={0})]  # 03:00 local — low-traffic window
    on_startup = startup
    # Must be a plain RedisSettings instance, not a method — see
    # app/workers/indexer.py's WorkerSettings for why.
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
