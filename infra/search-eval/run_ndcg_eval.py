"""S-08 CI regression gate: run every gold-set query against a live search
API, compute mean NDCG@10, and fail if it dropped more than 0.02 from the
last recorded baseline (DoD §3.2).

Usage:
    python run_ndcg_eval.py --gold-set gold_set.json --api-url http://localhost:8000 \
        --baseline baseline.json [--update-baseline]
"""

import argparse
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "backend"))
from app.search.ndcg import ndcg_for_query  # noqa: E402

REGRESSION_TOLERANCE = 0.02


def run_eval(gold_set_path: Path, api_url: str) -> dict:
    gold_set = json.loads(gold_set_path.read_text(encoding="utf-8"))

    per_query_scores = []
    with httpx.Client(timeout=10) as client:
        for case in gold_set["queries"]:
            resp = client.get(f"{api_url}/api/v1/search", params={"q": case["query"]})
            resp.raise_for_status()
            ranked_ids = [r["entity_id"] for r in resp.json()["results"]]
            score = ndcg_for_query(ranked_ids, case["relevance"], k=10)
            per_query_scores.append({"query": case["query"], "ndcg_at_10": score})

    mean_ndcg = sum(s["ndcg_at_10"] for s in per_query_scores) / len(per_query_scores) if per_query_scores else 0.0
    return {"mean_ndcg_at_10": mean_ndcg, "per_query": per_query_scores}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold-set", type=Path, required=True)
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args()

    result = run_eval(args.gold_set, args.api_url)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.baseline and args.baseline.exists():
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        drop = baseline["mean_ndcg_at_10"] - result["mean_ndcg_at_10"]
        if drop > REGRESSION_TOLERANCE:
            print(f"REGRESSION: NDCG@10 dropped {drop:.4f} (tolerance {REGRESSION_TOLERANCE})", file=sys.stderr)
            return 1

    if args.baseline and args.update_baseline:
        args.baseline.write_text(json.dumps({"mean_ndcg_at_10": result["mean_ndcg_at_10"]}, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
