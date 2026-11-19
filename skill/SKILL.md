---
name: deepseek-talent-graph
description: Query a Neo4j Relate graph of DeepSeek paper bylines to answer talent-mapping questions with Cypher — find key researchers by technical direction, cross-direction bridge authors, collaboration communities, coauthor networks and multi-hop paths. Use when asked who the core researchers are behind a model family, which authors span multiple directions, who collaborates with whom, or how a research area maps onto papers. The graph is a bundled single-file .rl store; query it read-only.
---

# DeepSeek Talent Graph (Relate)

A queryable graph built from a cleaned snapshot of **27 public DeepSeek papers / technical reports** — 409 de-duplicated byline authors, 328 in the R&E author pool. It is stored as a single Relate file so an agent can query connected context with Cypher, no server required.

> 口径红线：论文署名作者数 ≠ 公司员工数。共著网络 ≠ 组织架构。高频作者 ≠ 贡献排名。回答时必须带上这些限定。

## When to use

- "Who are the core researchers behind DeepSeek's base models?"
- "Which authors span the most technical directions?"
- "Show me the collaboration community around system efficiency."
- "Who are Chong Ruan's closest coauthors?"
- "What's the collaboration path between Damai Dai and Qihao Zhu?"
- "Which papers carry the math/proof direction?"

## Setup

Requires the `relate` CLI (see repo README). The graph file is `outputs/talent-graph.rl`. If missing, build it first:

```bash
python scripts/build_graph.py
```

## Graph model

Inspect the live schema before writing queries:

```bash
relate --database ./outputs/talent-graph.rl --read-only --mode envelope \
  "CALL db.schema.visualization();"
```

Nodes: `Author{name,paper_count,topic_count,first_seen,last_seen,high_freq,degree,weighted_degree}`, `Topic{name}`, `Paper{title}`, `Community{letter,name,size,summary}`.

Relationships:
- `(Author)-[:COAUTHOR {weight,topics}]->(Author)` — stored both directions
- `(Author)-[:WORKS_ON {papers}]->(Topic)`
- `(Author)-[:MEMBER_OF]->(Community)`
- `(Author)-[:AUTHORED]->(Paper)`

## Golden queries

All values are bound with `$params`, results bounded with `LIMIT`. Open with `--read-only --mode envelope`.

**1. Talents by direction** — most prolific authors in a topic:

```bash
relate --database ./outputs/talent-graph.rl --read-only --mode envelope \
  --param topic=主模型 --param limit=10 \
  'MATCH (a:Author)-[w:WORKS_ON]->(t:Topic {name: $topic})
   RETURN a.name AS author, w.papers AS papers_in_topic, a.degree AS coauthor_degree
   ORDER BY w.papers DESC, a.degree DESC LIMIT $limit'
```

**2. Cross-direction bridges** — authors spanning the most directions:

```bash
relate --database ./outputs/talent-graph.rl --read-only --mode envelope \
  --param min_topics=4 --param limit=15 \
  'MATCH (a:Author)-[:WORKS_ON]->(t:Topic)
   WITH a, count(t) AS n, collect(t.name) AS topics
   WHERE n >= $min_topics
   RETURN a.name AS author, n, topics ORDER BY n DESC LIMIT $limit'
```

**3. Coauthor neighbors** — closest collaborators of an author:

```bash
relate --database ./outputs/talent-graph.rl --read-only --mode envelope \
  --param name="Chong Ruan" --param limit=10 \
  'MATCH (a:Author {name: $name})-[c:COAUTHOR]->(b:Author)
   RETURN b.name AS coauthor, c.weight AS shared_papers
   ORDER BY c.weight DESC LIMIT $limit'
```

**4. Multi-hop path** — collaboration route between two authors:

```bash
relate --database ./outputs/talent-graph.rl --read-only --mode envelope \
  --param from="Damai Dai" --param to="Qihao Zhu" \
  'MATCH p = (a:Author {name: $from})-[:COAUTHOR*1..3]-(b:Author {name: $to})
   RETURN [n IN nodes(p) | n.name] AS path, length(p) AS hops
   ORDER BY hops LIMIT 5'
```

**5. Community roster** — representative authors of a collaboration group:

```bash
relate --database ./outputs/talent-graph.rl --read-only --mode envelope \
  --param letter=B \
  'MATCH (a:Author)-[:MEMBER_OF]->(g:Community {letter: $letter})
   RETURN g.name AS community, g.summary AS direction, collect(a.name) AS authors'
```

More ready-to-run queries live in `src/queries.py`.

## Safety rules

- Always open with `--read-only` for questions. Never write during a query.
- Bind values with `$param` + `--param`, never paste values into Cypher.
- Bound non-aggregate reads with `LIMIT`.
- Parse the `rows` field of the envelope JSON; `columns` holds column order.
- Treat the three 口径红线 at the top as mandatory caveats in every answer.
