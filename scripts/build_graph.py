"""Build a Relate graph from the bundled DeepSeek paper-byline dataset.

Data source: deepseek-talent-map skill (bones), a cleaned snapshot of 27 public
DeepSeek papers/technical reports -> 409 de-duplicated byline authors, 328 in
the R&E author pool. This script turns the flat CSV tables into a connected
graph that an agent can query with Cypher.

Graph model
-----------
Nodes:
  Author   {name, paper_count, topic_count, first_seen, last_seen, high_freq, degree, weighted_degree}
  Topic    {name}                       # e.g. 主模型 / 代码 / 数学/证明 ...
  Paper    {title}                      # from coauthor_edges.papers
  Community{letter, name, size, summary}

Relationships:
  (:Author)-[:COAUTHOR {weight, topics, papers}]->(:Author)   # undirected, stored both ways
  (:Author)-[:WORKS_ON {papers}]->(:Topic)                    # from author_topic_matrix counts
  (:Author)-[:MEMBER_OF]->(:Community)                        # from communities.top_authors
  (:Author)-[:AUTHORED]->(:Paper)                             # from coauthor_edges.papers
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "src"))


def read_rows(name: str) -> list[dict[str, str]]:
    path = DATA / f"{name}.txt"
    # files carry a UTF-8 BOM on the header
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def split_cn(value: str) -> list[str]:
    """Split Chinese/ASCII delimited lists on both 、 and ； and /."""
    out: list[str] = []
    for part in (value or "").replace("；", ";").split("、"):
        for p in part.split(";"):
            p = p.strip()
            if p:
                out.append(p)
    return out


def build(conn, progress: bool = True) -> dict[str, int]:
    def say(msg: str) -> None:
        if progress:
            print(msg)

    # 1) Author nodes -----------------------------------------------------
    authors = read_rows("coauthor_nodes")
    for r in authors:
        conn.execute(
            """MERGE (a:Author {name: $name})
               SET a.paper_count = $pc, a.topic_count = $tc,
                   a.first_seen = $fs, a.last_seen = $ls,
                   a.high_freq = $hf, a.degree = $deg, a.weighted_degree = $wd""",
            {
                "name": r["author"].strip(),
                "pc": int(r["paper_count"]),
                "tc": int(r["topic_count"]),
                "fs": r["first_seen"].strip(),
                "ls": r["last_seen"].strip(),
                "hf": r["is_high_freq_ge4"].strip().upper() == "TRUE",
                "deg": int(r["degree"]),
                "wd": int(r["weighted_degree"]),
            },
        )
    say(f"  authors: {len(authors)}")

    # 2) Community nodes + MEMBER_OF -------------------------------------
    communities = read_rows("communities")
    for c in communities:
        letter = c["group_letter"].strip()
        conn.execute(
            """MERGE (g:Community {letter: $letter})
               SET g.name = $name, g.size = $size, g.summary = $summary""",
            {
                "letter": letter,
                "name": c["group_name"].strip(),
                "size": int(c["member_count"]),
                "summary": c["direction_summary"].strip(),
            },
        )
        for author in split_cn(c["top_authors"]):
            conn.execute(
                """MATCH (a:Author {name: $an}), (g:Community {letter: $letter})
                   MERGE (a)-[:MEMBER_OF]->(g)""",
                {"an": author, "letter": letter},
            )
    say(f"  communities: {len(communities)}")

    # 3) Topic nodes + WORKS_ON relationship counts ----------------------
    matrix = read_rows("author_topic_matrix")
    topic_cols = [k for k in matrix[0].keys() if k not in ("author", "paper_count", "topic_count")]
    n_topic_links = 0
    for r in matrix:
        author = r["author"].strip()
        for topic in topic_cols:
            cnt = int(r[topic] or 0)
            if cnt <= 0:
                continue
            conn.execute("MERGE (t:Topic {name: $name})", {"name": topic})
            conn.execute(
                """MATCH (a:Author {name: $an}), (t:Topic {name: $tn})
                   MERGE (a)-[w:WORKS_ON]->(t)
                   SET w.papers = $cnt""",
                {"an": author, "tn": topic, "cnt": cnt},
            )
            n_topic_links += 1
    say(f"  topic links: {n_topic_links}")

    # 4) Paper nodes + AUTHORED + COAUTHOR edges -------------------------
    edges = read_rows("coauthor_edges")
    n_papers = 0
    n_edges = 0
    for e in edges:
        src, dst = e["source"].strip(), e["target"].strip()
        weight = int(e["weight_shared_papers"])
        topics = e["topics"].strip()
        papers = split_cn(e["papers"])
        for p in papers:
            conn.execute("MERGE (p:Paper {title: $t})", {"t": p})
            conn.execute(
                """MATCH (a:Author {name: $an}), (p:Paper {title: $t})
                   MERGE (a)-[:AUTHORED]->(p)""",
                {"an": src, "t": p},
            )
            conn.execute(
                """MATCH (a:Author {name: $an}), (p:Paper {title: $t})
                   MERGE (a)-[:AUTHORED]->(p)""",
                {"an": dst, "t": p},
            )
        # store one directed edge each way so both endpoints can traverse out
        for a, b in ((src, dst), (dst, src)):
            conn.execute(
                """MATCH (x:Author {name: $a}), (y:Author {name: $b})
                   MERGE (x)-[c:COAUTHOR]->(y)
                   SET c.weight = $w, c.topics = $topics""",
                {"a": a, "b": b, "w": weight, "topics": topics},
            )
            n_edges += 1
    n_papers = conn.execute("MATCH (p:Paper) RETURN count(p) AS n").fetchone()["n"]
    say(f"  papers: {n_papers}, coauthor edges (directed): {n_edges}")

    counts = {
        "authors": conn.execute("MATCH (a:Author) RETURN count(a) AS n").fetchone()["n"],
        "communities": conn.execute("MATCH (g:Community) RETURN count(g) AS n").fetchone()["n"],
        "topics": conn.execute("MATCH (t:Topic) RETURN count(t) AS n").fetchone()["n"],
        "papers": n_papers,
        "coauthor_edges": n_edges,
        "works_on": conn.execute("MATCH ()-[w:WORKS_ON]->() RETURN count(w) AS n").fetchone()["n"],
        "member_of": conn.execute("MATCH ()-[m:MEMBER_OF]->() RETURN count(m) AS n").fetchone()["n"],
    }
    return counts


def main() -> None:
    import relate

    out = ROOT / "outputs" / "talent-graph.rl"
    out.parent.mkdir(parents=True, exist_ok=True)
    # rebuild from scratch so reruns are deterministic
    if out.exists():
        out.unlink()
        say_removed = True
    else:
        say_removed = False

    conn = relate.connect(database=str(out))
    try:
        conn.autocommit = False
        print("Building graph from bundled data...")
        counts = build(conn)
        bookmark = conn.commit()
        conn.autocommit = True
        print(f"Wrote {out} (fresh rebuild={say_removed}, bookmark={bookmark})")
        print("Graph counts:")
        for k, v in counts.items():
            print(f"  {k:>15}: {v}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
