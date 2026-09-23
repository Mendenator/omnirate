#!/usr/bin/env python
"""Fail if .env.example drifts from app.core.config.Settings.

.env.example is the only place new contributors see what OMNIRATE_*
variables exist — if someone adds a Settings field (or renames/removes one)
without updating it, the example silently goes stale. This script diffs
the two so CI catches that instead of a human noticing months later.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from app.core.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_EXAMPLE = REPO_ROOT / ".env.example"


def documented_keys() -> set[str]:
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    return set(re.findall(r"^([A-Za-z0-9_]+)=", text, flags=re.MULTILINE))


def expected_keys() -> set[str]:
    prefix = Settings.model_config.get("env_prefix", "")
    return {f"{prefix}{name.upper()}" for name in Settings.model_fields}


def main() -> int:
    if not ENV_EXAMPLE.exists():
        print(f"::error::{ENV_EXAMPLE} does not exist", file=sys.stderr)
        return 1

    expected = expected_keys()
    prefix = Settings.model_config.get("env_prefix", "")
    documented = documented_keys()
    documented_omnirate = {k for k in documented if k.startswith(prefix)}

    missing = expected - documented_omnirate
    unknown = documented_omnirate - expected

    ok = True
    if missing:
        ok = False
        print(".env.example is missing variables defined in Settings:", file=sys.stderr)
        for key in sorted(missing):
            print(f"  - {key}", file=sys.stderr)

    if unknown:
        ok = False
        print(".env.example documents variables with no matching Settings field:", file=sys.stderr)
        for key in sorted(unknown):
            print(f"  - {key}", file=sys.stderr)

    if not ok:
        print(
            "\nUpdate .env.example (or app/core/config.py) so the two stay in sync.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: .env.example documents all {len(expected)} Settings fields.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
