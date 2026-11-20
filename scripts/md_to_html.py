#!/usr/bin/env python3
"""Convert a lecture-knowledge-summary Markdown file to a print-ready HTML.

Keeps relative image paths (`figures/...png`) so that, when the HTML is opened
via `file://` from the same directory as the `.md`, Chromium resolves them and
embeds them at PDF-print time. This is what lets the companion PDF display
images in any reader (WPS, browsers, previewers) without depending on the
`.md`'s relative paths.

Injects a black/white/gray minimal CSS tuned for A4 print, preserving the
🔴🟠🟢 priority emoji, the four-line `EN · 资料 / EN · 录音 / 中 / 📍 Source`
blockquote blocks, tables, and code. Consecutive `>` lines get Markdown hard
breaks so each blockquote line stays on its own line in the PDF.

Usage:
    python3 md_to_html.py <input.md> [output.html]

If `output.html` is omitted, writes `<input>.html` next to the input file.
Requires the `markdown` Python package (use the managed venv that already has
it, or `pip install markdown`).
"""
import sys
import os


def add_blockquote_breaks(text):
    """Give every consecutive `>` line a Markdown hard break (two trailing spaces).

    The knowledge/review specs write the four-/five-line blocks as consecutive
    blockquote lines. Without hard breaks python-markdown merges them into a
    single <p> and the PDF loses the line structure. Fenced code blocks are
    left untouched.
    """
    lines = text.split("\n")
    in_fence = False
    for i in range(len(lines) - 1):
        stripped = lines[i].lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith(">") and lines[i + 1].lstrip().startswith(">"):
            if not lines[i].endswith("  "):
                lines[i] += "  "
    return "\n".join(lines)

CSS = """
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  font-family: "PingFang SC", "Microsoft YaHei", "Hiragino Sans GB",
               "Noto Sans CJK SC", "Source Han Sans SC",
               "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji",
               sans-serif;
  color: #1f2328;
  line-height: 1.7;
  font-size: 14px;
  max-width: 920px;
  margin: 0 auto;
  padding: 24px 8px;
}
h1 { font-size: 24px; border-bottom: 2px solid #1f2328; padding-bottom: 8px;
     margin-top: 0; }
h2 { font-size: 20px; border-bottom: 1px solid #d0d7de; padding-bottom: 4px;
     margin-top: 30px; }
h3 { font-size: 16px; color: #444; margin-top: 22px; }
h4 { font-size: 15px; margin: 16px 0 6px; }
p  { margin: 8px 0; }
blockquote {
  background: #f6f8fa;
  border-left: 4px solid #c9d1d9;
  margin: 10px 0;
  padding: 10px 14px;
  border-radius: 4px;
  color: #24292f;
}
blockquote p { margin: 5px 0; }
code {
  background: #f0f0f0;
  padding: 1px 5px;
  border-radius: 3px;
  font-family: "SF Mono", "Menlo", "Consolas", monospace;
  font-size: 12.5px;
}
pre { background: #f6f8fa; padding: 12px; border-radius: 6px;
      overflow-x: auto; }
pre code { background: none; padding: 0; }
img {
  max-width: 100%;
  border: 1px solid #d0d7de;
  border-radius: 4px;
  margin: 10px 0;
  break-inside: avoid;
}
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 13px; }
th { background: #2f363d; color: #fff; padding: 6px 10px; text-align: left; }
td { border: 1px solid #d0d7de; padding: 6px 10px; vertical-align: top; }
tr:nth-child(even) td { background: #f6f8fa; }
hr { border: none; border-top: 1px solid #d0d7de; margin: 20px 0; }
ul, ol { padding-left: 22px; }
em { color: #57606a; }
/* Keep headings/blocks from breaking awkwardly across pages */
h2, h3, h4 { break-after: avoid; }
blockquote, table, img { break-inside: avoid; }
"""


def main():
    try:
        import markdown
    except ImportError:
        print("ERROR: python package 'markdown' not found. Install: pip install markdown",
              file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: md_to_html.py <input.md> [output.html]", file=sys.stderr)
        sys.exit(1)

    md_path = sys.argv[1]
    if not os.path.isfile(md_path):
        print(f"ERROR: input not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    out_path = (
        sys.argv[2]
        if len(sys.argv) > 2
        else os.path.splitext(md_path)[0] + ".html"
    )

    with open(md_path, encoding="utf-8") as f:
        text = f.read()

    html_body = markdown.markdown(
        add_blockquote_breaks(text), extensions=["tables", "fenced_code", "toc"]
    )

    doc = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>{os.path.basename(md_path)}</title>
<style>{CSS}</style>
</head>
<body>
{html_body}
</body>
</html>
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)

    print(f"Wrote {out_path} ({len(doc)} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
