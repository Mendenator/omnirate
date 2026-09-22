"""P2-07 scheduled export — arq cron every 15 minutes (the lag budget itself)."""

from arq import cron
from arq.connections import RedisSettings

from app.analytics.export_pipeline import run_export
from app.core.config import get_settings


async def run_export_job(ctx) -> None:
    results = run_export()
    for r in results:
        print(f"[analytics-export] {r.table}: {r.rows_exported} rows, watermark={r.watermark.isoformat()}")


class WorkerSettings:
    cron_jobs = [cron(run_export_job, minute={0, 15, 30, 45})]

    @staticmethod
    def redis_settings() -> RedisSettings:
        return RedisSettings.from_dsn(get_settings().redis_url)
