#!/usr/bin/env python3
"""Run all named queries against the built graph and print readable results."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from queries import QUERIES, run_query  # noqa: E402


def main() -> None:
    import relate

    store = ROOT / "outputs" / "talent-graph.rl"
    if not store.exists():
        print("Graph not found. Run: python scripts/build_graph.py")
        raise SystemExit(1)

    conn = relate.connect(database=str(store), read_only=True)
    try:
        for key, meta in QUERIES.items():
            print(f"\n=== {key} ===")
            print(f"    {meta['description']}")
            rows = run_query(conn, key)
            for row in rows[:15]:
                # Record is a dict subclass; use data() for clean values
                print("   ", json.dumps(dict(row), ensure_ascii=False, default=str))
            if not rows:
                print("    (no rows)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
