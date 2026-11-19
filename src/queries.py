"""Parameterised Cypher queries over the talent graph.

Every query binds values with $params (never string interpolation), bounds
non-aggregate results with LIMIT, and is safe to run with --read-only.
These are the "agent tools" the packaged skill teaches an agent to call.
"""

from __future__ import annotations

from typing import Any

QUERIES: dict[str, dict[str, Any]] = {
    "talents_by_topic": {
        "description": "Find the most prolific authors in a technical direction, with their collaboration degree.",
        "sql": """
            MATCH (a:Author)-[w:WORKS_ON]->(t:Topic {name: $topic})
            RETURN a.name AS author, w.papers AS papers_in_topic,
                   a.paper_count AS total_papers, a.degree AS coauthor_degree,
                   a.high_freq AS high_freq
            ORDER BY w.papers DESC, a.degree DESC
            LIMIT $limit
        """,
        "params": {"topic": "主模型", "limit": 10},
    },
    "cross_direction_bridge": {
        "description": "Authors spanning the most technical directions (bridge talent).",
        "sql": """
            MATCH (a:Author)-[:WORKS_ON]->(t:Topic)
            WITH a, count(t) AS n_topics, collect(t.name) AS topics
            WHERE n_topics >= $min_topics
            RETURN a.name AS author, n_topics, topics, a.paper_count AS total_papers
            ORDER BY n_topics DESC, a.paper_count DESC
            LIMIT $limit
        """,
        "params": {"min_topics": 4, "limit": 15},
    },
    "community_roster": {
        "description": "List a collaboration community and its representative authors.",
        "sql": """
            MATCH (a:Author)-[:MEMBER_OF]->(g:Community {letter: $letter})
            RETURN g.name AS community, g.summary AS direction,
                   collect(a.name) AS authors
            LIMIT 1
        """,
        "params": {"letter": "B"},
    },
    "coauthor_neighbors": {
        "description": "Top coauthors of a given author, strongest collaboration first.",
        "sql": """
            MATCH (a:Author {name: $name})-[c:COAUTHOR]->(b:Author)
            RETURN b.name AS coauthor, c.weight AS shared_papers, c.topics AS topics
            ORDER BY c.weight DESC
            LIMIT $limit
        """,
        "params": {"name": "Chong Ruan", "limit": 10},
    },
    "multi_hop_path": {
        "description": "Shortest collaboration path between two authors (up to 3 hops; 4 hops explodes on this dense graph).",
        "sql": """
            MATCH p = (a:Author {name: $from})-[:COAUTHOR*1..3]-(b:Author {name: $to})
            RETURN [n IN nodes(p) | n.name] AS path, length(p) AS hops
            ORDER BY hops
            LIMIT 5
        """,
        "params": {"from": "Damai Dai", "to": "Qihao Zhu"},
    },
    "papers_in_direction": {
        "description": "Which papers carry a given technical topic, and how often.",
        "sql": """
            MATCH (a:Author)-[w:WORKS_ON]->(t:Topic {name: $topic}),
                  (a)-[:AUTHORED]->(p:Paper)
            RETURN p.title AS paper, count(DISTINCT a) AS authors_from_direction
            ORDER BY authors_from_direction DESC, paper
            LIMIT $limit
        """,
        "params": {"topic": "数学/证明", "limit": 15},
    },
    "graph_stats": {
        "description": "Overview counts for the whole graph.",
        "sql": """
            MATCH (n) RETURN labels(n)[0] AS label, count(n) AS nodes
            ORDER BY nodes DESC
        """,
        "params": {},
    },
}


def run_query(conn, key: str, params: dict[str, Any] | None = None):
    """Execute a named query with defaults overridable by caller."""
    if key not in QUERIES:
        raise KeyError(f"unknown query: {key}")
    q = QUERIES[key]
    merged = dict(q["params"])
    if params:
        merged.update(params)
    cur = conn.execute(q["sql"], merged)
    return cur.fetchall()


def run_all(conn):
    """Run every query with its default params; return {key: list[dict]}."""
    out = {}
    for key in QUERIES:
        rows = run_query(conn, key)
        out[key] = [dict(r) for r in rows]
    return out
