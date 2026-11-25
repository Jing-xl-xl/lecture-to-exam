#!/usr/bin/env python3
"""Dump the visible text of a JS-rendered page.

Many share links (Zoom player, meeting summaries, exam briefings) return an app
shell to a plain HTTP client; the content only exists after JavaScript runs.
This drives a headless browser and writes document.body.innerText.

Usage:
    python3 scripts/fetch_webpage_text.py "<url>" -o page.txt [--scroll 8]

Exit: 0 ok | 1 dependency/launch problem
"""
import os
import sys
import argparse
import subprocess
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DUMPER = os.path.join(HERE, "_dump_page.js")


def main():
    ap = argparse.ArgumentParser(description="Render a page and dump its visible text")
    ap.add_argument("url")
    ap.add_argument("-o", "--output", default="page.txt")
    ap.add_argument("--scroll", type=int, default=8, help="scroll steps to trigger lazy content")
    args = ap.parse_args()

    scheme = (urlparse(args.url).scheme or "").lower()
    if scheme not in ("http", "https"):
        print(f"ERROR: refusing a {scheme or 'relative'} URL; only http(s) may be fetched.",
              file=sys.stderr)
        return 1

    node = _common.resolve_node()
    if not node:
        print("ERROR: node not found", file=sys.stderr)
        return 1
    if not os.path.isfile(DUMPER):
        print(f"ERROR: helper missing: {DUMPER}", file=sys.stderr)
        return 1
    proc = subprocess.run([node, DUMPER, args.url, args.output, str(args.scroll)],
                          capture_output=True, text=True)
    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)
    if proc.returncode != 0:
        return 1
    try:
        size = os.path.getsize(args.output)
    except OSError:
        size = 0
    if size < 80:
        print("WARN: page text is nearly empty; the site may need a login.", file=sys.stderr)
    print(f"Wrote {args.output} ({size} bytes)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
