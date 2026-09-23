"""CDC -> Parquet -> DuckDB batch export (P2-07).

Runs every 15 minutes (acceptance: lag <=15min) via the arq cron job in
app/analytics/worker.py. Uses DuckDB's postgres_scanner extension to pull
rows directly out of Postgres and write Parquet straight to S3 — no
intermediate Python row-by-row loop, which is what makes the "100M row
aggregate <=10s" target reachable later (columnar Parquet + DuckDB's vectorized
engine, not a Postgres OLTP table, answers those aggregate queries).

Incremental export cursor is a plain watermark (max `created_at` exported so
far) stored in `analytics_export_state` — simpler than reading Debezium's own
offset, and sufficient here because this pipeline only needs append-only
export, not full CDC semantics (updates/deletes are out of scope for P2-07's
reporting use case).
"""

from dataclasses import dataclass
from datetime import UTC, datetime

import duckdb

from app.core.config import Settings, get_settings

EXPORTED_TABLES = ("entities", "reviews")


@dataclass(frozen=True)
class ExportResult:
    table: str
    rows_exported: int
    watermark: datetime


def _connect(settings: Settings) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("INSTALL postgres_scanner; LOAD postgres_scanner;")
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"ATTACH '{settings.database_url_psycopg}' AS pg (TYPE POSTGRES, READ_ONLY)")
    return con


def _read_watermark(con: duckdb.DuckDBPyConnection, table: str) -> datetime:
    row = con.execute("SELECT watermark FROM pg.analytics_export_state WHERE table_name = ?", [table]).fetchone()
    return row[0] if row else datetime(1970, 1, 1, tzinfo=UTC)


def _write_watermark(con: duckdb.DuckDBPyConnection, table: str, watermark: datetime) -> None:
    con.execute(
        """
        INSERT INTO pg.analytics_export_state (table_name, watermark)
        VALUES (?, ?)
        ON CONFLICT (table_name) DO UPDATE SET watermark = excluded.watermark
        """,
        [table, watermark],
    )


def export_table(con: duckdb.DuckDBPyConnection, *, table: str, bucket: str, prefix: str) -> ExportResult:
    watermark = _read_watermark(con, table)
    now = datetime.now(UTC)
    date_partition = now.strftime("%Y-%m-%d")

    result = con.execute(
        f"""
        COPY (
            SELECT * FROM pg.{table} WHERE created_at > ? AND created_at <= ?
        ) TO 's3://{bucket}/{prefix}/{table}/date={date_partition}/part-{now:%H%M%S}.parquet'
        (FORMAT PARQUET)
        """,
        [watermark, now],
    )
    row = result.fetchone() if result.description else None
    rows = row[0] if row else 0

    _write_watermark(con, table, now)
    return ExportResult(table=table, rows_exported=rows, watermark=now)


def run_export() -> list[ExportResult]:
    settings = get_settings()
    con = _connect(settings)
    try:
        return [
            export_table(con, table=table, bucket=settings.analytics_bucket, prefix="cdc-export")
            for table in EXPORTED_TABLES
        ]
    finally:
        con.close()
