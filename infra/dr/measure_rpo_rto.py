"""RPO/RTO measurement for the DR drill (P3-12). See infra/dr/dr_drill.md for
the full procedure this script instruments.

Usage:
    python measure_rpo_rto.py --record-baseline --db-url postgresql://... --out baseline.json
    python measure_rpo_rto.py --verify --baseline-file baseline.json --db-url postgresql://... \
        --restore-started-at 2026-09-22T03:00:00Z --restore-finished-at 2026-09-22T03:22:00Z
"""

import argparse
import json
import sys
from datetime import datetime, timedelta

import psycopg2

RPO_TARGET_MINUTES = 5
RTO_TARGET_MINUTES = 30

_LATEST_ROW_QUERY = """
    SELECT max(created_at) FROM (
        SELECT created_at FROM reviews
        UNION ALL SELECT created_at FROM entities
    ) AS all_rows
"""


def get_latest_row_timestamp(db_url: str) -> datetime:
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(_LATEST_ROW_QUERY)
            (latest,) = cur.fetchone()
            return latest
    finally:
        conn.close()


def record_baseline(db_url: str, out_path: str) -> None:
    latest = get_latest_row_timestamp(db_url)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"latest_row_at": latest.isoformat()}, f)
    print(f"Baseline recorded: latest row at {latest.isoformat()}")


def verify(db_url: str, baseline_path: str, restore_started_at: datetime, restore_finished_at: datetime) -> int:
    with open(baseline_path, encoding="utf-8") as f:
        baseline = json.load(f)
    baseline_ts = datetime.fromisoformat(baseline["latest_row_at"])

    restored_ts = get_latest_row_timestamp(db_url)

    rpo = baseline_ts - restored_ts  # data lost = gap between what we had and what we recovered
    rto = restore_finished_at - restore_started_at

    rpo_minutes = rpo.total_seconds() / 60
    rto_minutes = rto.total_seconds() / 60

    print(f"RPO: {rpo_minutes:.1f} min (target <={RPO_TARGET_MINUTES})")
    print(f"RTO: {rto_minutes:.1f} min (target <={RTO_TARGET_MINUTES})")

    passed = rpo_minutes <= RPO_TARGET_MINUTES and rto_minutes <= RTO_TARGET_MINUTES
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", required=True)
    parser.add_argument("--record-baseline", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--out", default="baseline.json")
    parser.add_argument("--baseline-file", default="baseline.json")
    parser.add_argument("--restore-started-at", type=datetime.fromisoformat)
    parser.add_argument("--restore-finished-at", type=datetime.fromisoformat)
    args = parser.parse_args()

    if args.record_baseline:
        record_baseline(args.db_url, args.out)
        return 0
    if args.verify:
        if not (args.restore_started_at and args.restore_finished_at):
            print("--verify requires --restore-started-at and --restore-finished-at", file=sys.stderr)
            return 2
        return verify(args.db_url, args.baseline_file, args.restore_started_at, args.restore_finished_at)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
