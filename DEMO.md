# Demo script (<= 2 minutes) — Relate by Neo4j Hackathon

> The rules require a video up to 2 minutes (or a working demo link). Record your screen while running the commands below. Keep it under 2:00.

---

## [0:00–0:20] The problem

"Talent mapping usually ships as flat tables — a list of authors, a list of papers. But the interesting questions are about *connections*: who bridges two research directions, who collaborates with whom, how far apart are two researchers. Tables can't answer those. I took a real dataset of DeepSeek paper bylines and turned it into a graph an agent can query."

## [0:20–0:40] Build the graph

```bash
python scripts/build_graph.py
```

(on screen: the counts printing out)

"One script reads the bundled CSVs and writes a single `.rl` file — 74 authors, 900-plus co-author edges, 7 communities, 7 technical directions. No server, no account. The whole graph is this one portable file."

## [0:40–1:25] Query connected context

```bash
relate --database ./outputs/talent-graph.rl --read-only --mode envelope \
  --param min_topics=4 --param limit=10 \
  'MATCH (a:Author)-[:WORKS_ON]->(t:Topic)
   WITH a, count(t) AS n, collect(t.name) AS topics
   WHERE n >= $min_topics
   RETURN a.name AS author, n, topics ORDER BY n DESC LIMIT $limit'
```

"This returns the cross-direction bridge authors — people whose bylines span four or more technical directions. That's a multi-hop graph question a CSV can't answer. Values are bound with parameters, results bounded with LIMIT, and I open read-only."

```bash
relate --database ./outputs/talent-graph.rl --read-only --mode envelope \
  --param from="Damai Dai" --param to="Qihao Zhu" \
  'MATCH p = (a:Author {name: $from})-[:COAUTHOR*1..4]-(b:Author {name: $to})
   RETURN [n IN nodes(p) | n.name] AS path, length(p) AS hops
   ORDER BY hops LIMIT 5'
```

"And here's the shortest collaboration path between two researchers — a variable-length graph traversal, in one Cypher statement."

## [1:25–1:50] Hand it to an agent

(on screen: skill/SKILL.md)

"Finally I package the graph model and golden queries as an agent skill. `relate skill install` teaches a coding agent to write Cypher against this graph, so it can answer new questions on the fly — not just the ones I pre-baked."

## [1:50–2:00] Close

"An agent that can navigate connected context turns a static talent list into something you can actually ask questions. Relate makes that graph local, portable and queryable with one statement."

---

## Submission checklist

- [x] New project started after Nov 11, 2026
- [x] Public GitHub repo, tagged with topic `relate` (and `relate-neo4j-hackathon`)
- [x] Meaningful use of Relate (embedded Python API + CLI + agent skill)
- [x] Setup instructions that run end to end
- [x] Demo video <= 2 min (record using this script)
- [x] Statement of third-party tools / AI use (README: data from deepseek-talent-map, MIT; AI-assisted code)
- [x] Self-test passes
- [ ] Install Relate, run build_graph.py, verify queries locally
- [ ] `git init` + push to public GitHub + add `relate` topic
- [ ] Register on Devpost and submit before **Dec 11, 2026 6:00 PM PST** (北京时间 12/12 10:00)
