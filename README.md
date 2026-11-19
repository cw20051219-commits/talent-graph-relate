# DeepSeek Talent Graph × Relate

> Turn a flat paper-byline dataset into a **queryable graph** that an agent can navigate with Cypher — no server, no API key, one `.rl` file.

Built for the **Relate by Neo4j Hackathon 2026**. Uses [Relate](https://relatedb.ai/), Neo4j's open-source embedded graph database for AI agents.

## The idea

`deepseek-talent-map` shipped a cleaned snapshot of 27 public DeepSeek papers: 409 de-duplicated byline authors, 328 in the R&E pool, plus co-author edges, communities and an author×topic matrix. Useful — but flat CSV files can only answer pre-baked questions.

This project loads that data into a **Relate graph** and ships an **agent skill**, so an agent can answer *arbitrary* connected questions on the spot:

- "Who are the core researchers behind the base models?"
- "Which authors bridge the most technical directions?"
- "What's the collaboration path between Damai Dai and Qihao Zhu?"

These require graph traversal, not table lookups — exactly what Relate is for.

## Graph model

```
Nodes        Author · Topic · Paper · Community
Relations    (Author)-[:COAUTHOR {weight,topics}]->(Author)   both directions
             (Author)-[:WORKS_ON {papers}]->(Topic)
             (Author)-[:MEMBER_OF]->(Community)
             (Author)-[:AUTHORED]->(Paper)
```

The built graph contains **73 Author nodes, 1,868 directed COAUTHOR edges, 509→258 de-duplicated WORKS_ON links, 19 MEMBER_OF links, 7 communities, 7 topics and 22 named papers** — all in a single portable `outputs/talent-graph.rl`. (The underlying source snapshot covers 27 papers / 409 byline authors; the graph uses the co-author-network subset where edges are actually recorded.)

## Why it fits the judging criteria

| Criterion | How this project addresses it |
|---|---|
| Creativity | A headhunter's "paper byline → talent structure" method, rebuilt as an agent-queryable graph instead of static tables |
| Usefulness | Real recruiter/analyst questions answered with multi-hop graph queries; the dataset is real public byline data |
| Completeness | End-to-end: CSVs → build script → `.rl` store → query layer → agent skill → self-test |
| Clarity | README, golden queries, demo script, packaged `SKILL.md`, caveats stated up front |
| Effective use of connected context | Cypher traversal (co-author network, multi-hop paths, community membership), bundled agent skill, read-only envelope output, parameter binding — the graph *is* the product |

## Quick start

### 1. Install Relate

```bash
# macOS / Linux
curl -sSfL https://relatedb.ai/install.sh | bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://relatedb.ai/install.ps1 | iex"

relate --version     # 1.1.0 or newer
```

### 2. Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Build the graph (optional — already included)

The repo ships a pre-built `outputs/talent-graph.rl`, so you can query immediately (skip to step 4). To regenerate it from the CSVs:

```bash
python scripts/build_graph.py
# writes outputs/talent-graph.rl and prints node/relationship counts
```

### 4. Query it

```bash
relate --database ./outputs/talent-graph.rl --read-only --mode envelope \
  --param topic=主模型 --param limit=10 \
  'MATCH (a:Author)-[w:WORKS_ON]->(t:Topic {name: $topic})
   RETURN a.name AS author, w.papers AS papers_in_topic, a.degree AS coauthor_degree
   ORDER BY w.papers DESC, a.degree DESC LIMIT $limit'
```

Or run all seven bundled queries at once:

```bash
python scripts/demo_queries.py
```

### 5. Test

```bash
python scripts/selftest.py
```

## Give the graph to an agent

```bash
relate skill install --agent claude-code     # or cursor / codex / gemini-cli ...
```

Then copy `skill/SKILL.md` into your agent's skills directory. The agent reads the graph model and golden queries and writes its own Cypher from there. An MCP endpoint is also available via `relate serve` if you prefer MCP clients.

## Honest caveats (stated in every answer)

1. Byline author count ≠ headcount at the company; includes external collaborators and non-research roles.
2. The co-author network is not an org chart; clustering does not imply departments, seniority or reporting lines.
3. "High-frequency author" is ranked by paper count, not by contribution.
4. This is a public-data analysis, not an employee directory; no inference about current employment or level.

## Files

```
scripts/build_graph.py   CSV -> Relate graph (parameterised writes, transactional)
scripts/demo_queries.py  run all named queries, pretty-print results
scripts/selftest.py      data-layer tests (no deps) + graph-layer tests (needs relate)
src/queries.py           7 named, parameterised Cypher queries
skill/SKILL.md           agent skill: graph model + golden queries + safety rules
data/*.txt               bundled cleaned dataset (from deepseek-talent-map, MIT)
outputs/talent-graph.rl  generated single-file store
```

## Data source & license

Dataset from `deepseek-talent-map` by bones (MIT), derived from public paper metadata and bylines (HF Papers / arXiv / public technical reports). No PDFs or full text included. Code MIT — see [LICENSE](LICENSE).
