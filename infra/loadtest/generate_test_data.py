"""10M-row synthetic test data generator (P0-13 acceptance: <=20 minutes).

Uses Postgres COPY (not row-by-row INSERT) since at 10M rows the difference
is the entire time budget: COPY streams from a generator in one pass, while
per-row INSERT+commit would take hours over a network connection.

Usage:
    python generate_test_data.py --rows 10_000_000 --dsn postgresql://omnirate:omnirate@localhost/omnirate
"""

import argparse
import csv
import io
import random
import sys
import time
import uuid

import psycopg2

BRANCHES = ["hool-zoog", "eruul-mend", "bolovsrol", "tur-alba"]
CATEGORIES = {
    "hool-zoog": ["restoran", "kafe", "turgen-hool"],
    "eruul-mend": ["emneleg", "shudnii-emneleg", "emiin-san"],
    "bolovsrol": ["surguuli", "tsetserleg", "ikh-surguuli"],
    "tur-alba": ["uikh-gishuun", "itkh-gishuun"],
}
NAME_SYLLABLES = ["хаан", "алтан", "төв", "монгол", "энх", "их", "гоо", "сор", "жаргал", "наран"]


def random_name() -> str:
    return " ".join(random.choices(NAME_SYLLABLES, k=random.randint(1, 3))).title()


def generate_rows(n: int):
    for _ in range(n):
        branch = random.choice(BRANCHES)
        category = random.choice(CATEGORIES[branch])
        yield (
            str(uuid.uuid4()),
            branch,
            category,
            1,
            random_name(),
            f"ulaanbaatar-{random.randint(1, 9)}",
            round(random.uniform(47.8, 47.95), 6),
            round(random.uniform(106.8, 106.95), 6),
            "{}",
            random.random() < 0.3,
        )


def copy_entities(dsn: str, total_rows: int, batch_size: int = 200_000) -> None:
    conn = psycopg2.connect(dsn)
    conn.autocommit = False
    cur = conn.cursor()

    started = time.monotonic()
    written = 0
    rows_iter = generate_rows(total_rows)

    while written < total_rows:
        batch = [next(rows_iter, None) for _ in range(min(batch_size, total_rows - written))]
        batch = [r for r in batch if r is not None]
        if not batch:
            break

        buf = io.StringIO()
        writer = csv.writer(buf, delimiter="\t")
        writer.writerows(batch)
        buf.seek(0)

        cur.copy_expert(
            """
            COPY entities (id, branch_slug, category_slug, schema_version, name,
                           location_slug, lat, lon, attributes, verified)
            FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t')
            """,
            buf,
        )
        conn.commit()
        written += len(batch)
        elapsed = time.monotonic() - started
        print(f"{written:,}/{total_rows:,} rows in {elapsed:.1f}s", file=sys.stderr)

    cur.close()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=10_000_000)
    parser.add_argument("--dsn", required=True, help="e.g. postgresql://omnirate:omnirate@localhost/omnirate")
    parser.add_argument("--batch-size", type=int, default=200_000)
    args = parser.parse_args()

    t0 = time.monotonic()
    copy_entities(args.dsn, args.rows, args.batch_size)
    total = time.monotonic() - t0
    print(f"Done: {args.rows:,} rows in {total / 60:.1f} min", file=sys.stderr)
    if total > 20 * 60:
        print("WARNING: exceeded the 20-minute P0-13 acceptance target", file=sys.stderr)
