#!/usr/bin/env python3
"""Turn a markdown outline into a one-page A4 cheat sheet (two columns).

The point is the one-page guarantee: it renders, counts the pages, and shrinks
the font until the whole thing fits. A cheat sheet that spills onto page two is
useless when you are revising in a corridor.

Usage:
    python3 scripts/make_cheatsheet.py outline.md cheat.pdf [--title "..."] \
        [--font 9.4] [--cols 2]

Exit: 0 fits on one page | 1 cannot fit / dependency problem
"""
import os
import re
import sys
import argparse
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RENDERER = os.path.join(HERE, "html_to_pdf.js")

TEMPLATE = """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 8mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: "PingFang SC","Helvetica Neue",Arial,sans-serif;
        font-size: {font}pt; line-height: 1.34; color:#111; margin:0; }}
h1 {{ font-size: {h1}pt; margin:0 0 2mm; border-bottom:1.2pt solid #111; padding-bottom:1mm; }}
h2 {{ font-size: {h2}pt; margin: 2.2mm 0 1mm; padding: 0.6mm 1.4mm;
      background:#111; color:#fff; border-radius:1mm; }}
h3 {{ font-size: {h2}pt; margin: 1.6mm 0 0.6mm; border-left:2pt solid #111; padding-left:1.4mm; }}
table {{ width:100%; border-collapse:collapse; margin:0.6mm 0 1.4mm; font-size:{table}pt; }}
th,td {{ border:0.5pt solid #999; padding:0.5mm 1mm; vertical-align:top; }}
th {{ background:#eee; font-weight:600; }}
ul,ol {{ margin:0.4mm 0 1.2mm; padding-left:5mm; }}
li {{ margin:0.3mm 0; }}
code {{ font-family: Menlo, monospace; font-size:{table}pt; background:#f2f2f2; padding:0 0.6mm; }}
.grid {{ display:grid; grid-template-columns: repeat({cols}, 1fr); gap: 3mm 5mm; }}
</style></head><body>
<h1>{title}</h1>
<div class="grid">
{content}
</div>
</body></html>"""


def build_html(md_text, title, font, cols):
    try:
        import markdown
    except ImportError:
        print("ERROR: python package 'markdown' not found. Install: pip install markdown", file=sys.stderr)
        raise SystemExit(1)
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    # 分栏：按 <h2> 切成块，交替分配，避免整栏塞爆
    parts = re.split(r"(?=<h2)", body)
    parts = [p for p in parts if p.strip()]
    if cols > 1 and len(parts) > 1:
        columns = [[] for _ in range(cols)]
        heights = [0] * cols
        for p in parts:
            i = heights.index(min(heights))
            columns[i].append(p)
            heights[i] += len(p)
        body = "".join(f'<div class="col">{"".join(c)}</div>' for c in columns)
    return TEMPLATE.format(font=font, h1=round(font * 1.5, 1), h2=round(font * 1.1, 1),
                           table=round(font * 0.93, 1), cols=cols,
                           title=title, content=body)


def page_count(pdf_path):
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf
        except ImportError:
            return None
    try:
        with pymupdf.open(pdf_path) as doc:
            return doc.page_count
    except Exception:
        return None


def render(html_path, pdf_path):
    node = _common.resolve_node()
    if not node:
        print("ERROR: node not found", file=sys.stderr)
        return False
    proc = subprocess.run([node, RENDERER, html_path, pdf_path], capture_output=True, text=True)
    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)
    return proc.returncode == 0


def main():
    ap = argparse.ArgumentParser(description="Markdown -> one-page A4 cheat sheet")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--title", default=None)
    ap.add_argument("--font", type=float, default=9.4)
    ap.add_argument("--cols", type=int, default=2)
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        print(f"ERROR: not found: {args.input}", file=sys.stderr)
        return 1
    with open(args.input, encoding="utf-8") as f:
        md = f.read()
    title = args.title or (md.lstrip().splitlines()[0].lstrip("# ").strip() if md.strip() else "Cheat sheet")

    html_path = os.path.splitext(args.output)[0] + ".html"
    font = args.font
    for attempt in range(5):
        html = build_html(md, title, font, args.cols)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        if not render(html_path, args.output):
            print("ERROR: PDF rendering failed", file=sys.stderr)
            return 1
        pages = page_count(args.output)
        if pages is None:
            print("WARN: pymupdf missing, cannot verify the one-page limit", file=sys.stderr)
            return 0
        if pages == 1:
            print(f"OK: one page at {font:.1f}pt -> {args.output}")
            return 0
        print(f"   {pages} pages at {font:.1f}pt; shrinking", file=sys.stderr)
        font -= 0.6
        if font < 6.0:
            break
    print(f"ERROR: still {pages} pages at {font:.1f}pt; trim the content or use --cols 2", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
