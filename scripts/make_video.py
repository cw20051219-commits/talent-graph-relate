"""
Build the 2-minute narrated demo video for the Relate hackathon submission.

Approach: no screen recording needed. Each scene is a high-resolution slide
(PIL) that shows exactly what the DEMO.md script talks about, with a synthetic
English voice-over (edge-tts). ffmpeg muxes slides + audio into one MP4.

Run:  python scripts/make_video.py
Out:  outputs/demo.mp4
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from pathlib import Path


def run_ffmpeg(cmd: list[str]) -> None:
    """Run ffmpeg with retry: on Windows a just-written media file may still be locked."""
    for attempt in range(5):
        try:
            subprocess.run(cmd, check=True)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.8 * (attempt + 1))

import edge_tts
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
BUILD = OUT / "_video_build"

def _find_ffmpeg() -> str:
    import sys
    # exact known-good path first
    candidates = list(Path(sys.prefix).glob(
        "Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64*.exe"))
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe:
            candidates.insert(0, Path(exe))
    except Exception:
        pass
    for p in candidates:
        if p.exists():
            return str(p)
    raise RuntimeError("ffmpeg not found; pip install imageio-ffmpeg")

FFMPEG = _find_ffmpeg()
VOICE = "en-US-GuyNeural"
W, H = 1280, 720
FPS = 24

FONT_MONO = "/c/Windows/Fonts/consola.ttf".replace("/c/", "C:/")
FONT_SANS = "/c/Windows/Fonts/simhei.ttf".replace("/c/", "C:/")

# Palette (terminal-like dark theme)
BG = (13, 17, 23)
PANEL = (22, 27, 35)
FG = (230, 237, 243)
MUTED = (139, 148, 158)
ACCENT = (88, 166, 255)
GREEN = (63, 185, 80)
YELLOW = (210, 153, 34)
BORDER = (48, 54, 61)


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = (cur + " " + word).strip()
            if draw.textlength(trial, font=fnt) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def draw_base(title: str, kicker: str, idx: int, total: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # top accent bar
    d.rectangle([0, 0, W, 6], fill=ACCENT)
    d.text((56, 30), kicker, font=font(FONT_SANS, 20), fill=ACCENT)
    d.text((56, 62), title, font=font(FONT_SANS, 42), fill=FG)
    d.line([56, 122, W - 56, 122], fill=BORDER, width=2)
    # footer
    d.text((56, H - 44), "grounded-talent-graph  |  Relate by Neo4j Hackathon", font=font(FONT_MONO, 16), fill=MUTED)
    d.text((W - 130, H - 44), f"{idx}/{total}", font=font(FONT_MONO, 16), fill=MUTED)
    return img, d


def code_panel(d: ImageDraw.ImageDraw, lines: list[str], x: int, y: int, w: int, h: int,
               fnt: ImageFont.FreeTypeFont, title: str = "") -> None:
    d.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=PANEL, outline=BORDER, width=2)
    cy = y + 14
    if title:
        d.text((x + 18, cy), title, font=font(FONT_MONO, 15), fill=YELLOW)
        cy += 26
        d.line([x + 14, cy - 4, x + w - 14, cy - 4], fill=BORDER, width=1)
    for ln in lines:
        d.text((x + 18, cy), ln, font=fnt, fill=GREEN if ln.startswith(">") else FG)
        cy += fnt.size + 6


SCENES = [
    {
        "title": "Talent mapping as a graph",
        "kicker": "TALENT GRAPH  /  RELATE",
        "voice": "Talent mapping usually ships as flat tables: a list of authors, a list of papers. "
                 "But the interesting questions are about connections. Who bridges two research directions? "
                 "Who collaborates with whom? How far apart are two researchers? Tables can't answer those. "
                 "So I turned a real dataset of DeepSeek paper bylines into a graph an agent can query.",
        "kind": "title",
    },
    {
        "title": "One script. One portable file.",
        "kicker": "STEP 1  /  BUILD THE GRAPH",
        "voice": "One script reads the bundled CSVs and writes a single dot R L file: "
                 "seventy-three authors, over nine hundred co-author edges, seven communities, "
                 "and seven technical directions. No server, no account. "
                 "The whole graph is this one portable file.",
        "kind": "build",
    },
    {
        "title": "Query connected context",
        "kicker": "STEP 2  /  CROSS-DIRECTION BRIDGES",
        "voice": "This query returns cross-direction bridge authors: people whose bylines span "
                 "four or more technical directions. That's a multi-hop graph question a CSV simply can't answer. "
                 "Yukun Li tops the list at seven directions. Values are bound with parameters, "
                 "results are bounded with LIM-IT, and I open the database read-only.",
        "kind": "query1",
    },
    {
        "title": "Shortest collaboration path",
        "kicker": "STEP 3  /  MULTI-HOP TRAVERSAL",
        "voice": "And here is the shortest collaboration path between two researchers: "
                 "a variable-length graph traversal, in one single Cypher statement. "
                 "Damai Dai and Qihao Zhu turn out to be direct co-authors, one hop apart. "
                 "This is connected context, queried in milliseconds on a local file.",
        "kind": "query2",
    },
    {
        "title": "Hand the graph to an agent",
        "kicker": "STEP 4  /  AGENT SKILL",
        "voice": "Finally, I package the graph model and golden queries as an agent skill. "
                 "Relate skill install teaches a coding agent to write Cypher against this graph, "
                 "so it can answer brand-new questions on the fly, not just the ones I pre-baked. "
                 "An M C P endpoint is available too.",
        "kind": "skill",
    },
    {
        "title": "From static list to answerable graph",
        "kicker": "CLOSE",
        "voice": "An agent that can navigate connected context turns a static talent list "
                 "into something you can actually ask questions. "
                 "Relate makes that graph local, portable, and queryable with one statement.",
        "kind": "close",
    },
]


def render_scene(scene: dict, idx: int, total: int) -> Path:
    img, d = draw_base(scene["title"], scene["kicker"], idx, total)
    kind = scene["kind"]
    mono = font(FONT_MONO, 18)
    mono_sm = font(FONT_MONO, 15)

    if kind == "title":
        code_panel(d, [
            "flat tables     ->   connected graph",
            "who bridges?    ->   CROSS_DIRECTION_BRIDGE",
            "who works with? ->   COAUTHOR neighbors",
            "how far apart?  ->   multi-hop path",
        ], 56, 160, 1168, 190, mono, "QUESTION TYPES")
        d.text((56, 400), "Built on Relate - an embedded, agent-native graph database.",
               font=font(FONT_SANS, 24), fill=MUTED)
        d.text((56, 444), "One .rl file. Cypher + vector + full-text search. Local and portable.",
               font=font(FONT_SANS, 24), fill=MUTED)

    elif kind == "build":
        code_panel(d, [
            "$ python scripts/build_graph.py",
            "> authors      73",
            "> papers       22",
            "> coauthor_edges   1868 (directed)",
            "> communities  7",
            "> works_on     258",
            "> wrote outputs/talent-graph.rl  (640 KB)",
        ], 56, 160, 700, 260, mono, "TERMINAL")
        code_panel(d, [
            "Author   -[:COAUTHOR]->   Author",
            "Author   -[:WORKS_ON]->   Topic",
            "Author   -[:MEMBER_OF]->  Community",
            "Author   -[:AUTHORED]->   Paper",
        ], 780, 160, 444, 260, mono_sm, "GRAPH MODEL")
        d.text((56, 460), "No server. No cloud account. The graph is a single file you can email.",
               font=font(FONT_SANS, 22), fill=MUTED)

    elif kind == "query1":
        code_panel(d, [
            "MATCH (a:Author)-[:WORKS_ON]->(t:Topic)",
            "WITH a, count(t) AS n, collect(t.name) AS topics",
            "WHERE n >= $min_topics",
            "RETURN a.name, n, topics",
            "ORDER BY n DESC LIMIT $limit",
        ], 56, 150, 700, 200, mono_sm, "CYPHER  (params: min_topics=4, limit=10)")
        code_panel(d, [
            "> Yukun Li   7 topics",
            "> Chong Ruan 6 topics",
            "> Yu Wu      6 topics",
            "> Zhenda Xie 5 topics",
            "> ...",
        ], 56, 368, 700, 200, mono, "RESULT")
        code_panel(d, [
            "Why it matters:",
            "Bridge authors span many",
            "directions - the people",
            "who connect teams.",
            "A CSV cannot answer this.",
        ], 780, 150, 444, 418, mono_sm, "INSIGHT")

    elif kind == "query2":
        code_panel(d, [
            "MATCH p = (a:Author {name:$from})",
            "        -[:COAUTHOR*1..3]-(b:Author {name:$to})",
            "RETURN [n IN nodes(p) | n.name] AS path,",
            "       length(p) AS hops",
            "ORDER BY hops LIMIT 5",
        ], 56, 150, 720, 200, mono_sm, "CYPHER  (from=Damai Dai, to=Qihao Zhu)")
        code_panel(d, [
            "> Damai Dai -> Qihao Zhu     1 hop",
            "> Damai Dai -> Zhihong Shao",
            ">             -> Qihao Zhu  2 hops",
        ], 56, 368, 720, 160, mono, "RESULT")
        d.text((56, 560), "Variable-length traversal, bounded to 3 hops to stay fast on a dense graph.",
               font=font(FONT_SANS, 20), fill=MUTED)

    elif kind == "skill":
        code_panel(d, [
            "$ relate skill install --agent claude-code",
            "",
            "# then copy skill/SKILL.md into the",
            "# agent's skills directory",
            "",
            "> agent reads graph model + golden",
            "> queries, then writes its own Cypher",
        ], 56, 160, 760, 280, mono, "TERMINAL")
        code_panel(d, [
            "The skill teaches:",
            "- node & edge types",
            "- 7 golden queries",
            "- parameter binding",
            "- read-only safety",
        ], 840, 160, 384, 280, mono_sm, "AGENT SKILL")
        d.text((56, 480), "The agent answers NEW questions - not just the ones I pre-baked.",
               font=font(FONT_SANS, 22), fill=MUTED)

    elif kind == "close":
        code_panel(d, [
            "static talent list   ->   answerable graph",
            "flat CSV             ->   connected context",
            "one-off queries      ->   agent skill",
        ], 56, 170, 1168, 180, mono, "WHAT CHANGED")
        d.text((56, 410), "github.com/cw20051219-commits/talent-graph-relate",
               font=font(FONT_MONO, 22), fill=GREEN)
        d.text((56, 456), "Topic: relate  |  23 tests pass  |  MIT licensed",
               font=font(FONT_SANS, 22), fill=MUTED)

    path = BUILD / f"scene_{idx}.png"
    img.save(path)
    return path


async def synth_voice(scene: dict, idx: int) -> Path:
    mp3 = BUILD / f"voice_{idx}.mp3"
    communicate = edge_tts.Communicate(scene["voice"], VOICE, rate="+4%")
    await communicate.save(str(mp3))
    return mp3


def mux_scene(png: Path, mp3: Path, idx: int) -> Path:
    """Mux a still slide + voice clip. -shortest makes video length == audio length."""
    out = BUILD / f"clip_{idx}.mp4"
    cmd = [
        FFMPEG, "-y", "-loglevel", "error",
        "-loop", "1", "-framerate", str(FPS), "-i", str(png),
        "-i", str(mp3),
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", str(out),
    ]
    run_ffmpeg(cmd)
    return out


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    total = len(SCENES)

    # 1) audio + slides (reuse cached assets if present)
    async def build_all():
        slides, voices = [], []
        for i, s in enumerate(SCENES, 1):
            png = BUILD / f"scene_{i}.png"
            mp3 = BUILD / f"voice_{i}.mp3"
            if not (png.exists() and png.stat().st_size > 1000):
                render_scene(s, i, total)
            if not (mp3.exists() and mp3.stat().st_size > 1000):
                await synth_voice(s, i)
            slides.append(png)
            voices.append(mp3)
            print(f"scene {i}/{total} ready")
        return slides, voices

    slides, voices = asyncio.run(build_all())

    # 2) mux each slide with its voice (-shortest => clip length == voice length)
    clips = [mux_scene(slides[i], voices[i], i + 1) for i in range(total)]

    # 4) concat
    listfile = BUILD / "concat.txt"
    listfile.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    final = OUT / "demo.mp4"
    run_ffmpeg([
        FFMPEG, "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(listfile),
        "-c", "copy", str(final),
    ])
    print("WROTE", final, f"({final.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
