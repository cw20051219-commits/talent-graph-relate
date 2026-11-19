#!/usr/bin/env python3
"""Self-test for the talent graph project.

Two layers:
  * data layer  - always runnable (pure Python, no deps): validates the CSV
                  parsing and the graph-building plan against the real data.
  * graph layer - runs only if `relate` is installed: builds a fresh graph and
                  executes every named query, checking that results are sane.

Run: python scripts/selftest.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "src"))

passed = 0
failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name} {detail}")


def rows(name):
    with (DATA / f"{name}.txt").open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


print("== data layer (no deps) ==")
nodes = rows("coauthor_nodes")
edges = rows("coauthor_edges")
comm = rows("communities")
matrix = rows("author_topic_matrix")
check("coauthor_nodes non-empty", len(nodes) > 0, f"got {len(nodes)}")
check("coauthor_edges non-empty", len(edges) > 0, f"got {len(edges)}")
check("communities parsed", len(comm) >= 5, f"got {len(comm)}")
check("topic matrix parsed", len(matrix) > 0, f"got {len(matrix)}")
check("node has degree field", "degree" in nodes[0])
check("edge has weight field", "weight_shared_papers" in edges[0])
check("no BOM in header keys", "author" in nodes[0], f"keys={list(nodes[0])[:3]}")

names = {r["author"].strip() for r in nodes}
edge_endpoints = {edges[0]["source"].strip(), edges[0]["target"].strip()}
check("edge endpoints exist in nodes", edge_endpoints <= names, f"missing={edge_endpoints - names}")

topic_cols = [k for k in matrix[0] if k not in ("author", "paper_count", "topic_count")]
check("topic columns detected", len(topic_cols) >= 5, f"topics={topic_cols}")

print("== graph layer (needs relate-db) ==")
try:
    import relate
except ImportError:
    print("  SKIP  relate-db not installed yet (run pip install -r requirements.txt)")
else:
    from queries import QUERIES, run_query

    store = ROOT / "outputs" / "talent-graph.rl"
    if not store.exists():
        print("  SKIP  graph not built yet (run: python scripts/build_graph.py)")
    else:
        conn = relate.connect(database=str(store), read_only=True)

        def scalar(cypher):
            row = conn.execute(cypher).fetchone()
            return next(iter(row.values()))

        check("authors in graph", scalar("MATCH (a:Author) RETURN count(a)") == len(nodes))
        check("papers in graph", scalar("MATCH (p:Paper) RETURN count(p)") > 0)
        check("coauthor edges in graph", scalar("MATCH ()-[c:COAUTHOR]->() RETURN count(c)") > 0)
        check("works_on links in graph", scalar("MATCH ()-[w:WORKS_ON]->() RETURN count(w)") > 0)
        check("member_of links in graph", scalar("MATCH ()-[m:MEMBER_OF]->() RETURN count(m)") > 0)

        for key in QUERIES:
            try:
                result = run_query(conn, key)
                check(f"query {key} runs", isinstance(result, list), f"rows={len(result) if isinstance(result, list) else 'n/a'}")
            except Exception as exc:  # noqa: BLE001
                check(f"query {key} runs", False, repr(exc))

        by_topic = run_query(conn, "talents_by_topic")
        check("talents_by_topic returns rows", len(by_topic) > 0)
        check("talents_by_topic has author field", "author" in by_topic[0] if by_topic else False)
        conn.close()

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
