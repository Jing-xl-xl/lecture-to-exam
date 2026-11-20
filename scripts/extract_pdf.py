#!/usr/bin/env python3
"""Extract per-page text and optionally render page images from a PDF.

Uses PyMuPDF (fitz). Renders every page to figures/{prefix}_p{NN}.png by
default so the images can be embedded in the Markdown, exactly as the
lecture knowledge workflow expects.

Usage:
    python3 scripts/extract_pdf.py course.pdf --prefix I [--figures ./figures] [--dpi 120] [--no-render]

Options:
    --prefix PREFIX     Filename prefix for rendered pages (default: first letter of filename)
    --figures DIR       Directory for rendered PNGs (default: ./figures next to output)
    --dpi N             Render DPI (default: 120)
    --no-render         Only extract text, do not render images
    --text-out FILE     Write extracted text to FILE (default: stdout)
    --python PATH       Python interpreter that has pymupdf (fitz) installed
"""
import os
import sys
import argparse
import subprocess


WORKER = r'''
import json, sys
try:
    import pymupdf as fitz
except ImportError:
    import fitz
pdf, prefix, figures, dpi, render = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]=="1"
doc = fitz.open(pdf)
pages = []
for i, page in enumerate(doc, 1):
    text = page.get_text()
    pages.append({"page": i, "text": text})
    if render:
        pix = page.get_pixmap(dpi=dpi)
        out = f"{prefix}_p{i:02d}.png"
        pix.save(__import__("os").path.join(figures, out))
print(json.dumps({"count": len(pages), "pages": pages}, ensure_ascii=False))
'''


def main():
    ap = argparse.ArgumentParser(description="Extract PDF text and render page images")
    ap.add_argument("pdf")
    ap.add_argument("--prefix")
    ap.add_argument("--figures")
    ap.add_argument("--dpi", type=int, default=120)
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--text-out")
    ap.add_argument("--python")
    args = ap.parse_args()

    if not os.path.isfile(args.pdf):
        raise SystemExit(f"ERROR: pdf not found: {args.pdf}")

    prefix = args.prefix or os.path.basename(args.pdf)[0].upper()
    figures = args.figures or os.path.join(os.path.dirname(os.path.abspath(args.pdf)), "figures")
    os.makedirs(figures, exist_ok=True)

    py = args.python or os.environ.get("PYTHON_BIN") or sys.executable
    import tempfile, json
    fd, worker = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    try:
        with open(worker, "w", encoding="utf-8") as f:
            f.write(WORKER)
        proc = subprocess.run(
            [py, worker, args.pdf, prefix, figures, str(args.dpi), "0" if args.no_render else "1"],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            print(proc.stderr, file=sys.stderr)
            raise SystemExit("ERROR: PyMuPDF worker failed. Install: pip install pymupdf")
        raw = proc.stdout
        # Some PyMuPDF versions print a deprecation warning to stdout; start
        # parsing at the first JSON brace so such noise cannot break us.
        brace = raw.find("{")
        if brace < 0:
            print(raw, file=sys.stderr)
            raise SystemExit("ERROR: worker produced no JSON output")
        data = json.loads(raw[brace:])
    finally:
        try:
            os.remove(worker)
        except OSError:
            pass

    blocks = []
    for p in data["pages"]:
        blocks.append(f"**Page {p['page']}**\n\n{p['text'].strip() or '(no extractable text — likely image-only; see rendered PNG)'}\n")
    text = "\n---\n\n".join(blocks)

    if args.text_out:
        with open(args.text_out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote {args.text_out} ({data['count']} pages)", file=sys.stderr)
    else:
        print(text)

    if not args.no_render:
        print(f"Rendered {data['count']} pages to {figures} ({args.dpi} dpi, prefix {prefix})", file=sys.stderr)


if __name__ == "__main__":
    main()
