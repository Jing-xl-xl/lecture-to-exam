#!/usr/bin/env python3
"""Validate review-mode input: needs at least TWO lecture Markdown files.

Review mode aggregates multiple lecture knowledge files plus exam material.
This guard makes the "must be multiple lectures" rule a hard, testable check
rather than a convention. Also checks each file looks like a knowledge note.

Usage:
    python3 scripts/validate_review_input.py file1.md file2.md [file3.md ...] [--exam FILE ...]

Exit codes:
    0  valid
    2  fewer than 2 lecture files (the core rule)
    3  a lecture file is missing / unreadable
"""
import os
import sys
import argparse


def looks_like_knowledge_note(path):
    try:
        with open(path, encoding="utf-8") as f:
            head = f.read(4000)
    except OSError:
        return False, "unreadable"
    if "EN · " not in head and "知识点" not in head and "知识考点" not in head:
        return False, "does not look like a lecture knowledge note (no EN · / 知识点 marker)"
    return True, "ok"


def main():
    ap = argparse.ArgumentParser(description="Validate review-mode inputs")
    ap.add_argument("lectures", nargs="+", help="lecture knowledge .md files (need >= 2)")
    ap.add_argument("--exam", action="append", default=[], help="exam outline / past-paper file (informational)")
    args = ap.parse_args()

    # expand directories: collect .md files inside them
    expanded = []
    for item in args.lectures:
        if os.path.isdir(item):
            expanded += [os.path.join(item, f) for f in sorted(os.listdir(item)) if f.endswith(".md")]
        else:
            expanded.append(item)

    if len(expanded) < 2:
        print(f"ERROR: review mode requires at least 2 lecture files, got {len(expanded)}.", file=sys.stderr)
        print("Pass multiple <course>_L<N>_知识点与考点.md files, or a directory containing them.", file=sys.stderr)
        return 2

    bad = False
    for path in expanded:
        if not os.path.isfile(path):
            print(f"ERROR: lecture file not found: {path}", file=sys.stderr)
            bad = True
            continue
        ok, why = looks_like_knowledge_note(path)
        if not ok:
            print(f"WARNING: {path}: {why}", file=sys.stderr)
    if bad:
        return 3

    print(f"OK: {len(expanded)} lecture files accepted for review mode"
          + (f"; {len(args.exam)} exam material(s) noted" if args.exam else ""))
    print("Files:")
    for p in expanded:
        print(f"  - {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
