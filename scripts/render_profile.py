#!/usr/bin/env python3
"""Render the profile README's animated SVG cards.

Run with STATIC=1 to render the last frame without animation.
"""

from __future__ import annotations

import base64
import html
import json
import os
import shutil
import subprocess
import tempfile
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".github" / "data" / "contributions.json"
LANGUAGES = ROOT / ".github" / "data" / "languages.json"
OUT = ROOT / "cards"
STATIC = os.environ.get("STATIC") == "1"

BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
TEXT = "#f0f6fc"
MUTED = "#8b949e"
GREEN = "#3fb950"
GREEN_DARK = "#1f6f3a"
PURPLE = "#a371f7"

FEATURED = [
    ("Guardrail-UI", "A TypeScript interface for building trustworthy AI guardrails.", "TypeScript"),
    ("Summit", "A Go control plane for orchestrating reliable engineering workflows.", "Go"),
    ("ContextSplit", "Private, local-first context intelligence for desktop workflows.", "Rust"),
    ("GraphMind", "A visual graph workspace for exploring connected ideas.", "TypeScript"),
    ("TripWise", "A practical travel planning experience built for the web.", "JavaScript"),
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def font_data() -> str:
    font = os.environ.get(
        "PROFILE_FONT",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    )
    if not Path(font).exists():
        raise FileNotFoundError(f"Font not found: {font}")
    with tempfile.TemporaryDirectory() as temp:
        subset = Path(temp) / "profile.woff"
        command = shutil.which("pyftsubset")
        if command:
            subprocess.run(
                [
                    command,
                    font,
                    f"--output-file={subset}",
                    "--flavor=woff",
                    "--layout-features=*",
                    "--unicodes=U+0020-007E",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )
        else:
            subprocess.run(
                [
                    os.environ.get("PYTHON", "python3"),
                    "-m",
                    "fontTools.subset",
                    font,
                    f"--output-file={subset}",
                    "--flavor=woff",
                    "--layout-features=*",
                    "--unicodes=U+0020-007E",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )
        return base64.b64encode(subset.read_bytes()).decode()


FONT = font_data()


def shell(title: str, body: str, height: int, delay: float = 0.0) -> str:
    motion = "" if STATIC else f'class="motion" style="--delay:{delay:.1f}s"'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" viewBox="0 0 900 {height}" role="img" aria-label="{esc(title)}">
<style>
@font-face{{font-family:Profile;src:url(data:font/woff;base64,{FONT}) format("woff")}}
*{{box-sizing:border-box}} text{{font-family:Profile,Arial,sans-serif}} .card{{fill:{PANEL};stroke:{BORDER};stroke-width:1}}
.title{{fill:{TEXT};font-size:25px;font-weight:700}} .body{{fill:{TEXT};font-size:17px}} .muted{{fill:{MUTED};font-size:14px}} .accent{{fill:{GREEN}}}
.motion{{opacity:0;animation:fade-up .8s ease-out var(--delay) forwards}} .float{{animation:float 4s ease-in-out infinite}}
@keyframes fade-up{{from{{opacity:0;transform:translateY(18px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-5px)}}}}
@keyframes draw{{from{{stroke-dashoffset:1000}}to{{stroke-dashoffset:0}}}}
@media(prefers-reduced-motion:reduce){{.motion{{opacity:1;animation:none!important}} .float{{animation:none!important}} animate{{display:none}}}}
</style>{body}</svg>"""


def rect(x: int, y: int, w: int, h: int, rx: int = 18) -> str:
    return f'<rect class="card" x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/>'


def write(name: str, content: str) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(content, encoding="utf-8")


def render_hero() -> None:
    portrait_motion = "float" if not STATIC else ""
    portrait = (
        f'<image class="{portrait_motion}" href="https://avatars.githubusercontent.com/u/203167559?v=4" '
        'x="735" y="34" width="122" height="122" preserveAspectRatio="xMidYMid slice" '
        'clip-path="circle(61px at 61px 61px)"/>'
    )
    body = f"""{rect(0, 0, 900, 190)}
<g class="motion" style="--delay:0s"><text class="muted" x="42" y="48">HELLO, WORLD</text>
<text class="title" x="42" y="94" font-size="42">Deepanshu Khatri</text>
<text class="body" x="42" y="130">Full Stack Developer · Tech Enthusiast</text>
<text class="muted" x="42" y="160">Building useful products at the intersection of code and curiosity.</text></g>
{portrait}"""
    write("hero.svg", shell("Deepanshu Khatri — Full Stack Developer", body, 190))


def render_tiles() -> None:
    tiles = [
        ("PROJECTS", "Explore the things I build.", "https://github.com/Deepanshu-2006?tab=repositories", GREEN),
        ("WRITING", "Ideas, systems, and experiments.", "https://github.com/Deepanshu-2006", PURPLE),
        ("CONNECT", "Let's make something thoughtful.", "https://github.com/Deepanshu-2006", "#58a6ff"),
    ]
    for i, (label, text, link, color) in enumerate(tiles):
        body = (
            f'<g class="motion" style="--delay:{0.4 + i * 0.15:.1f}s"><rect x="4" y="4" width="292" height="132" rx="16" fill="{PANEL}" stroke="{BORDER}"/>'
            f'<circle cx="34" cy="38" r="8" fill="{color}"/><text class="title" x="54" y="44" font-size="17">{label}</text>'
            f'<text class="body" x="24" y="82" font-size="15">{esc(text)}</text><a href="{link}"><text class="muted" x="24" y="112">Open profile →</text></a></g>'
        )
        write(f"tile-{i + 1}.svg", shell(label.title(), body, 140))


def contribution_stats(calendar: dict) -> tuple[list[dict], int, int, str]:
    days = [d for week in calendar.get("weeks", []) for d in week.get("contributionDays", [])]
    months = defaultdict(int)
    for item in days:
        months[item["date"][:7]] += item.get("contributionCount", 0)
    ordered = [{"label": key[5:7], "value": months[key]} for key in sorted(months)[-12:]]
    active = sum(item.get("contributionCount", 0) > 0 for item in days)
    streak = 0
    for item in reversed(days):
        if item.get("contributionCount", 0) > 0:
            streak += 1
        elif streak:
            break
    busiest = max(days, key=lambda item: item.get("contributionCount", 0), default={"date": "—"})
    return ordered, active, streak, busiest.get("date", "—")


def streak_metrics(calendar: dict) -> tuple[int, int]:
    days = [d for week in calendar.get("weeks", []) for d in week.get("contributionDays", [])]
    current = 0
    for item in reversed(days):
        if item.get("contributionCount", 0) > 0:
            current += 1
        else:
            break
    longest = 0
    run = 0
    for item in days:
        if item.get("contributionCount", 0) > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    return current, longest


def render_stats(calendar: dict) -> None:
    current, longest = streak_metrics(calendar)
    total = int(calendar.get("totalContributions", 0))
    body = f"""<rect x="18" y="18" width="864" height="354" rx="10" fill="#000" stroke="#e6edf3" stroke-width="2"/>
<line x1="300" y1="70" x2="300" y2="320" stroke="#e6edf3" stroke-width="2"/><line x1="600" y1="70" x2="600" y2="320" stroke="#e6edf3" stroke-width="2"/>
<g class="motion" style="--delay:.2s"><text x="150" y="175" text-anchor="middle" fill="#fff" font-size="42" font-weight="700">{total:,}</text><text x="150" y="222" text-anchor="middle" fill="#fff" font-size="22">Total Contributions</text><text x="150" y="270" text-anchor="middle" fill="#9aa4ad" font-size="17">Last 12 months</text></g>
<g class="motion" style="--delay:.4s"><circle cx="450" cy="122" r="48" fill="none" stroke="#ff9800" stroke-width="8" stroke-dasharray="314 24" transform="rotate(-90 450 122)"/><text x="450" y="137" text-anchor="middle" fill="#fff" font-size="42" font-weight="700">{current}</text><text x="450" y="211" text-anchor="middle" fill="#ff9800" font-size="22" font-weight="700">Current Streak</text><text x="450" y="253" text-anchor="middle" fill="#9aa4ad" font-size="17">Updated from GitHub</text></g>
<g class="motion" style="--delay:.6s"><text x="750" y="175" text-anchor="middle" fill="#fff" font-size="42" font-weight="700">{longest}</text><text x="750" y="222" text-anchor="middle" fill="#fff" font-size="22">Longest Streak</text><text x="750" y="270" text-anchor="middle" fill="#9aa4ad" font-size="17">All recorded activity</text></g>"""
    write("stats.svg", shell("GitHub contribution streak", body, 390))


def render_languages(languages: dict) -> None:
    ordered = sorted(languages.items(), key=lambda item: item[1], reverse=True)[:5]
    total = max(sum(value for _, value in ordered), 1)
    colors = ["#3776ab", "#00bfae", "#3178c6", "#e96228", "#f34b7d"]
    radius, circumference = 82, 2 * 3.141592653589793 * 82
    segments, legend, offset = [], [], 0
    for index, ((name, value), color) in enumerate(zip(ordered, colors)):
        length = value / total * circumference
        segments.append(f'<circle cx="395" cy="220" r="{radius}" fill="none" stroke="{color}" stroke-width="30" stroke-dasharray="{length:.2f} {circumference-length:.2f}" stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 395 220)"/>')
        y = 130 + index * 43
        legend.append(f'<rect x="52" y="{y-19}" width="25" height="25" rx="2" fill="{color}"/><text x="92" y="{y}" fill="#83909b" font-size="20">{esc(name)}</text>')
        offset += length
    body = f"""<rect x="18" y="18" width="520" height="364" rx="10" fill="#0d1117" stroke="#30363d" stroke-width="2"/>
<text x="42" y="75" fill="#087de0" font-size="29">Top Languages by Commit</text>
{''.join(legend)}
<g class="motion" style="--delay:.5s">{''.join(segments)}<circle cx="395" cy="220" r="52" fill="#0d1117"/></g>"""
    write("languages.svg", shell("Top Languages by Commit", body, 400))


def render_chart(calendar: dict) -> None:
    months, active, streak, busiest = contribution_stats(calendar)
    max_value = max((item["value"] for item in months), default=1)
    bars = []
    for i, item in enumerate(months):
        x = 56 + i * 66
        h = max(8, round(item["value"] / max_value * 104))
        y = 172 - h
        delay = 1.0 + i * 0.08
        bars.append(
            f'<g class="motion" style="--delay:{delay:.1f}s"><rect x="{x}" y="{y}" width="34" height="{h}" rx="7" fill="{GREEN}">'
            + ("" if STATIC else f'<animate attributeName="height" from="0" to="{h}" dur=".8s" begin="{delay:.1f}s" fill="freeze"/><animate attributeName="y" from="172" to="{y}" dur=".8s" begin="{delay:.1f}s" fill="freeze"/>')
            + f'</rect><text class="muted" x="{x+17}" y="198" text-anchor="middle">{item["label"]}</text></g>'
        )
    body = f"""{rect(0, 0, 900, 245)}
<g class="motion" style="--delay:.8s"><text class="title" x="32" y="42">Contribution rhythm</text><text class="muted" x="32" y="66">Last 12 months</text>
<text class="accent" x="610" y="39" font-size="22" font-weight="700">{streak}</text><text class="muted" x="610" y="59">day streak</text>
<text class="accent" x="710" y="39" font-size="22" font-weight="700">{active}</text><text class="muted" x="710" y="59">active days</text>
<text class="muted" x="610" y="84">Busiest: {esc(busiest)}</text></g>
<line x1="42" y1="172" x2="858" y2="172" stroke="{BORDER}"/>{"".join(bars)}"""
    write("contributions.svg", shell("Contribution rhythm", body, 245))


def render_repo(index: int, name: str, description: str, language: str) -> None:
    colors = {"TypeScript": "#3178c6", "Go": "#00add8", "Rust": "#dea584", "JavaScript": "#f1e05a"}
    color = colors.get(language, GREEN)
    body = f"""{rect(0, 0, 900, 150)}
<g class="motion" style="--delay:{1.8 + index * .15:.1f}s"><circle cx="42" cy="42" r="9" fill="{color}"/>
<text class="title" x="68" y="49">{esc(name)}</text><text class="muted" x="760" y="48">{esc(language)}</text>
<text class="body" x="42" y="86">{esc(description)}</text><a href="https://github.com/Deepanshu-2006/{esc(name)}"><text class="muted" x="42" y="120">View repository →</text></a></g>"""
    write(f"repo-{index+1}.svg", shell(f"{name} repository", body, 150))


def render_graph(calendar: dict) -> None:
    cells = []
    for week_index, week in enumerate(calendar.get("weeks", [])[-53:]):
        for day in week.get("contributionDays", []):
            weekday = int(day.get("weekday", 0))
            count = day.get("contributionCount", 0)
            level = min(4, count // 3 + (1 if count else 0))
            fill = ["#172033", "#123d4a", "#087f8b", "#16c7a2", "#7cf7d4"][level]
            x, y = 40 + week_index * 15, 58 + weekday * 15
            delay = (week_index * 0.035 + weekday * 0.02) % 1.8
            opacity = 0.45 + level * 0.12
            cells.append(
                f'<rect x="{x}" y="{y}" width="10" height="10" rx="3" fill="{fill}" opacity="{opacity:.2f}">' 
                f'<animate attributeName="opacity" values="{opacity:.2f};1;{opacity:.2f}" dur="3.8s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
                f'<animateTransform attributeName="transform" type="scale" values="1;1.12;1" dur="3.8s" begin="{delay:.2f}s" repeatCount="indefinite" additive="sum"/>'
                '</rect>'
            )
    body = f"""<defs>
<linearGradient id="graph-gradient" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#0d1828"/><stop offset="55%" stop-color="#111d2b"/><stop offset="100%" stop-color="#102d32"/></linearGradient>
<radialGradient id="graph-glow"><stop offset="0%" stop-color="#16c7a2" stop-opacity=".26"/><stop offset="100%" stop-color="#16c7a2" stop-opacity="0"/></radialGradient>
<filter id="soft-glow"><feGaussianBlur stdDeviation="8"/></filter>
</defs>
<rect x="0" y="0" width="900" height="190" rx="18" fill="url(#graph-gradient)" stroke="{BORDER}"/>
<circle cx="770" cy="104" r="130" fill="url(#graph-glow)" filter="url(#soft-glow)"><animate attributeName="r" values="110;145;110" dur="7s" repeatCount="indefinite"/></circle>
<g class="motion" style="--delay:2.8s"><text class="title" x="32" y="32" font-size="20">Contribution constellation</text><text class="muted" x="32" y="51">Every commit adds another point of light</text>
<path d="M40 166 C180 138 250 177 370 145 S600 128 860 153" fill="none" stroke="#16c7a2" stroke-opacity=".32" stroke-width="2" stroke-dasharray="5 9"><animate attributeName="stroke-dashoffset" from="0" to="-140" dur="8s" repeatCount="indefinite"/></path>
{''.join(cells)}</g>"""
    write("graph.svg", shell("Contribution constellation", body, 190))


def main() -> None:
    calendar = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {"weeks": []}
    languages = json.loads(LANGUAGES.read_text(encoding="utf-8")) if LANGUAGES.exists() else {}
    render_hero()
    render_tiles()
    render_stats(calendar)
    render_languages(languages)
    render_chart(calendar)
    for index, repo in enumerate(FEATURED):
        render_repo(index, *repo)
    render_graph(calendar)


if __name__ == "__main__":
    main()
