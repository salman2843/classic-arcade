"""Render docs/*.md into styled HTML pages.

Markdown is the source of truth: every game gets one narrative file with the
function tables, and this script turns those files into pages that can be read
on the live site.

    python tools/build_docs.py
"""

from __future__ import annotations

import re
from pathlib import Path
from string import Template

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

# (label in nav, path relative to docs/)
PAGES = [
    ("Architecture", "ARCHITECTURE.md"),
    ("Snake", "games/snake.md"),
    ("Tic-Tac-Toe", "games/tictactoe.md"),
]

PAGE = Template(
    """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="theme-color" content="#0b1120" />
<title>$title &mdash; Arcade / Classic</title>
<style>
:root{
  --bg:#070b14;--panel:#0c1526;--line:#1f2f4b;--text:#e6edf7;--muted:#93a4bd;
  --mint:#34d399;--coral:#fb7185;--cyan:#38bdf8;
  --mono:ui-monospace,"Cascadia Code","JetBrains Mono",Consolas,monospace;
  --sans:ui-sans-serif,system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:
  radial-gradient(900px 500px at 85% -10%,rgba(52,211,153,.12),transparent 60%),
  radial-gradient(700px 420px at 0 10%,rgba(56,189,248,.1),transparent 55%),
  var(--bg);
  color:var(--text);font-family:var(--sans);line-height:1.7;-webkit-font-smoothing:antialiased}
a{color:var(--mint);text-decoration:none}
a:hover{text-decoration:underline}
.bar{display:flex;align-items:center;justify-content:space-between;gap:16px;
  padding:14px clamp(16px,4vw,48px);border-bottom:1px solid var(--line);
  background:rgba(7,11,20,.8);backdrop-filter:blur(12px);position:sticky;top:0;z-index:5}
.brand{font-family:var(--mono);font-size:.9rem;letter-spacing:.16em;color:var(--text)}
.brand span{color:var(--mint)}
nav{display:flex;gap:clamp(10px,2.5vw,24px);font-size:.86rem;flex-wrap:wrap}
nav a{color:var(--muted)}
nav a:hover,nav a[aria-current="page"]{color:var(--text);text-decoration:none}
main{width:min(860px,calc(100% - 32px));margin:0 auto;padding:40px 0 64px}
.eyebrow{font-family:var(--mono);font-size:.72rem;letter-spacing:.22em;
  text-transform:uppercase;color:var(--mint);margin:0 0 8px}
.doc h1{font-size:clamp(2rem,5vw,2.9rem);letter-spacing:-.02em;line-height:1.15;margin:0 0 18px}
.doc h2{font-size:1.5rem;margin:44px 0 12px;padding-top:18px;border-top:1px solid var(--line)}
.doc h3{font-size:1.12rem;margin:28px 0 8px;color:var(--mint)}
.doc p,.doc li{color:#c6d3e6;font-size:1rem}
.doc strong{color:var(--text)}
.doc ul,.doc ol{padding-left:1.3rem}
.doc li{margin:.25rem 0}
.doc code{font-family:var(--mono);font-size:.86em;background:rgba(148,163,184,.13);
  padding:.12em .38em;border-radius:6px;color:#dbe7f7}
.doc pre{background:#0a1222;border:1px solid var(--line);border-radius:12px;
  padding:16px;overflow:auto;font-size:.82rem;line-height:1.6}
.doc pre code{background:none;padding:0;font-size:1em}
.doc table{width:100%;border-collapse:collapse;margin:18px 0;font-size:.88rem;display:block;overflow-x:auto}
.doc th,.doc td{border:1px solid var(--line);padding:9px 12px;text-align:left;vertical-align:top}
.doc th{background:rgba(52,211,153,.08);color:var(--mint);font-family:var(--mono);
  font-size:.74rem;letter-spacing:.08em;text-transform:uppercase}
.doc tr:nth-child(even) td{background:rgba(148,163,184,.035)}
.doc blockquote{margin:18px 0;padding:12px 18px;border-left:3px solid var(--mint);
  background:rgba(52,211,153,.06);border-radius:0 10px 10px 0;color:var(--muted)}
.doc blockquote p{margin:0;color:var(--muted)}
.doc hr{border:0;border-top:1px solid var(--line);margin:36px 0}
.doc img{max-width:100%;border-radius:12px}
.foot{display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px;
  margin-top:56px;padding-top:18px;border-top:1px solid var(--line);
  color:var(--muted);font-size:.82rem}
.foot a{color:var(--muted)}
@media(max-width:640px){.bar{flex-direction:column;align-items:flex-start}}
</style>
</head>
<body>
<header class="bar">
  <a class="brand" href="$home">ARCADE<span>/</span>CLASSIC</a>
  <nav>$nav</nav>
</header>
<main>
  <p class="eyebrow">$section</p>
  <article class="doc">
$content
  </article>
  <footer class="foot">
    <a href="$home">&larr; Back to the arcade</a>
    <span>Python &middot; pygame-ce &middot; Pyodide</span>
  </footer>
</main>
</body>
</html>
"""
)


def build_nav(prefix: str, current: Path) -> str:
    links = []
    for label, relative in PAGES:
        target = DOCS / relative
        href = f"{prefix}/{relative.removesuffix('.md')}.html".replace("//", "/")
        active = ' aria-current="page"' if target.samefile(current) else ""
        links.append(f'<a href="{href}"{active}>{label}</a>')
    return "".join(links)


def rewrite_links(html: str) -> str:
    """Point Markdown links at the generated .html files."""
    return re.sub(r'href="([^"]+?)\.md(#[^"]*)?"', r'href="\1.html\2"', html)


def build_page(source: Path) -> Path:
    text = source.read_text(encoding="utf-8")
    body = markdown.markdown(
        text,
        extensions=["extra", "sane_lists", "smarty", "toc"],
        output_format="html5",
    )
    body = rewrite_links(body)

    title = next(
        (line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("# ")),
        source.stem,
    )
    prefix = ".." if source.parent != DOCS else "."
    home = f"{prefix}/../index.html" if source.parent != DOCS else "../index.html"
    section = "Game notes" if source.parent != DOCS else "Build notes"

    output = source.with_suffix(".html")
    output.write_text(
        PAGE.substitute(
            title=title,
            prefix=prefix,
            home=home,
            nav=build_nav(prefix, source),
            section=section,
            content=body,
        ),
        encoding="utf-8",
    )
    return output


def main() -> None:
    built = []
    for _, relative in PAGES:
        source = DOCS / relative
        if not source.exists():
            raise SystemExit(f"Missing documentation source: {source}")
        built.append(build_page(source))

    for output in built:
        print(f"built {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
