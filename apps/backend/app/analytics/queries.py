"""Reporting queries over the Parquet lake (P2-07). DuckDB's vectorized
columnar scan is what makes "100M row aggregate <=10s" achievable — the same
query against the OLTP Postgres table would compete with live write traffic
and scan row-oriented storage.
"""

from typing import Any

import duckdb

from app.core.config import get_settings


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("SET s3_region='ap-southeast-1';")
    return con


def daily_review_counts_by_poe_level(
    con: duckdb.DuckDBPyConnection, *, since_date: str, bucket: str | None = None
) -> list[tuple[Any, ...]]:
    bucket = bucket or get_settings().analytics_bucket
    return con.execute(
        f"""
        SELECT date_trunc('day', created_at) AS day, poe_level, count(*) AS n
        FROM read_parquet('s3://{bucket}/cdc-export/reviews/date=*/*.parquet')
        WHERE created_at >= ?
        GROUP BY 1, 2
        ORDER BY 1, 2
        """,
        [since_date],
    ).fetchall()


def entity_counts_by_branch(con: duckdb.DuckDBPyConnection, *, bucket: str | None = None) -> list[tuple[Any, ...]]:
    bucket = bucket or get_settings().analytics_bucket
    return con.execute(
        f"""
        SELECT branch_slug, count(*) AS n
        FROM read_parquet('s3://{bucket}/cdc-export/entities/date=*/*.parquet')
        GROUP BY 1
        ORDER BY 2 DESC
        """
    ).fetchall()
