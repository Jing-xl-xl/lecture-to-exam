#!/usr/bin/env python3
"""Executable gate for a finished lecture-to-exam deliverable.

SKILL.md states the format rules in prose; models drift. This turns the rules
into checks an agent can run and trust, so a deliverable is either pass or fail
before it is shown to the user.

Usage:
    python3 <skill>/scripts/run.py verify_output <file.md> [options]

Options:
    --mode a|b          force a mode (default: auto-detect from the content)
    --slides N          Mode A: require the source page-map to have N rows
    --figures-dir DIR   Mode A: base dir for relative image paths
                        (default: the .md's own directory)
    --allow-text-only   Mode A escape hatch: permit a notes file with no slide
                        images. Only after the user explicitly agreed to a
                        text-only handout.
    --scope full|partial  partial: the page-map covers only the pages actually
                        taught (deck supplied but not covered). Requires a
                        "not taught" note in the file.
    --json              machine-readable result

Exit codes: 0 all checks pass, 1 violations found, 2 usage/input error.
"""
import os
import re
import sys
import json
import argparse

CJK = re.compile(r"[\u4e00-\u9fff]")
A_KEYS = ("EN · 资料", "EN · 录音", "**中**", "📍 Source")
B_KEYS = ("EN · 资料", "EN · 录音", "关键词", "中（一段话）", "📍 Source")
HINT_WORDS = ("考法", "作答", "考试", "应写", "写入答案", "应试", "答题")
IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
MAP_ROW_RE = re.compile(r"^\|\s*📄\S*\s*(?:p|P|slide|Slide)\.?\s*(\d+)", re.M)
MAP_IMG_CELL_RE = re.compile(r"\|\s*(figures/[^|\s]+)\s*\|")


def detect_mode(text):
    if "中（一段话）" in text:
        return "b"
    if "Source Page-Map" in text or "EN · 资料" in text:
        return "a"
    return None


def split_items(text):
    return re.split(r"^#### ", text, flags=re.M)[1:]


def check(checks, name, ok, detail=""):
    checks.append((name, bool(ok), detail))


def verify_mode_a(path, text, checks, args):
    root = args.figures_dir or os.path.dirname(os.path.abspath(path))

    items = split_items(text)
    check(checks, "A1 knowledge points present", len(items) >= 1, f"{len(items)} item(s)")
    missing = [
        (i + 1, k) for i, it in enumerate(items)
        for k in A_KEYS if k not in it
    ]
    check(checks, "A2 four-line block complete (EN·资料 / EN·录音 / 中 / 📍 Source)",
          not missing,
          "ok" if not missing else f"missing {missing[:5]}")

    imgs = IMG_RE.findall(text)
    check(checks, "A3 original slide image embedded",
          bool(imgs) or args.allow_text_only,
          f"{len(imgs)} image(s)" + (" (text-only explicitly allowed)" if args.allow_text_only else ""))

    broken, uncaptioned, unlabelled = [], [], []
    for rel in imgs:
        full = rel if os.path.isabs(rel) else os.path.join(root, rel)
        if not os.path.isfile(full):
            broken.append(rel)
        pos = text.find(f"]({rel})")
        before = text[max(0, pos - 400):pos]
        after = text[pos:pos + 400]
        if "资料图示" not in before:
            unlabelled.append(rel)
        if not re.search(r"\n\*图：[^\n]+\*\s*(?:\n|$)", after):
            uncaptioned.append(rel)
    check(checks, "A4 every image file exists on disk", not broken,
          "ok" if not broken else f"missing {broken[:5]}")
    check(checks, "A5 every image has **资料图示** + *图：…* caption",
          not uncaptioned and not unlabelled,
          "ok" if not (uncaptioned or unlabelled)
          else f"no caption {uncaptioned[:3]} / no label {unlabelled[:3]}")

    has_map = "Source Page-Map" in text
    check(checks, "A6 Source Page-Map chapter present", has_map)
    if has_map:
        rows = [m for m in MAP_ROW_RE.findall(text)]
        check(checks, "A7 page-map has one row per slide", bool(rows), f"{len(rows)} row(s)")
        check(checks, "A7b page-map has an Image column", "| Image |" in text)
        mapped = set(MAP_IMG_CELL_RE.findall(text))
        embedded = set(imgs)
        check(checks, "A8 every embedded image appears in the page-map",
              embedded.issubset(mapped) if embedded else True,
              "ok" if embedded.issubset(mapped) else f"not mapped: {sorted(embedded - mapped)[:3]}")
        bad_map = [p for p in mapped
                   if not os.path.isfile(os.path.join(root, p))]
        check(checks, "A9 every page-map image path exists", not bad_map,
              "ok" if not bad_map else f"missing {bad_map[:5]}")
        if args.scope == "partial":
            mentions = ("未讲" in text) or ("not taught" in text.lower()) or ("未覆盖" in text)
            check(checks, "A10 partial scope documents which decks were not taught",
                  mentions, "ok" if mentions else "add a '未讲 / not taught' note in §2")
        if args.slides and args.scope == "full":
            check(checks, f"A11 page-map row count == {args.slides} supplied slides",
                  len(rows) == args.slides, f"{len(rows)} row(s)")


def verify_mode_b(path, text, checks, args):
    check(checks, "B1 text-only: no image syntax, no figures/ paths",
          "![" not in text and "figures/" not in text)

    chapters = sorted(int(n) for n in re.findall(r"^## (\d+)\.", text, flags=re.M))
    check(checks, "B2 all 11 parts, in order",
          chapters == list(range(1, 12)), f"chapters={chapters}")

    items = split_items(text)
    check(checks, "B3 knowledge points present", len(items) >= 1, f"{len(items)} item(s)")

    bad_keys = [(i + 1, k) for i, it in enumerate(items)
                for k in B_KEYS if k not in it]
    check(checks, "B4 five-line block complete", not bad_keys,
          "ok" if not bad_keys else f"missing {bad_keys[:5]}")

    short, long_, inline_bullets = [], [], []
    for i, it in enumerate(items):
        m = re.search(r"\*\*中（一段话）\*\*\s*·\s*(.+)", it)
        if not m:
            continue
        para = m.group(1).split("\n")[0]
        n = len(CJK.findall(para))
        if n < 80:
            short.append((i + 1, n))
        elif n > 200:
            long_.append((i + 1, n))
        if re.search(r"^\s*[-*·]\s", para):
            inline_bullets.append(i + 1)
    check(checks, "B5 Chinese paragraph is 80-200 characters",
          not short and not long_,
          "ok" if not (short or long_) else f"short {short[:3]} long {long_[:3]}")
    check(checks, "B6 Chinese paragraph is one continuous block (no bullets)",
          not inline_bullets, "ok" if not inline_bullets else f"items {inline_bullets[:3]}")

    hot = [it for it in items if it.lstrip().startswith(("🔴", "🟠"))]
    unhinted = [i + 1 for i, it in enumerate(items)
                if it.lstrip().startswith(("🔴", "🟠"))
                and not any(w in it for w in HINT_WORDS)]
    check(checks, "B7 every 🔴/🟠 point carries an exam hint",
          bool(hot) and not unhinted,
          f"{len(hot)} hot point(s)" if not unhinted else f"no hint in items {unhinted[:3]}")

    placeholder = "本次输入未覆盖"
    if placeholder in text:
        check(checks, "B8 uncovered questions use the exact placeholder, unedited",
              text.count(placeholder) >= 1, f"{text.count(placeholder)} occurrence(s)")


def main():
    ap = argparse.ArgumentParser(description="Verify a lecture-to-exam deliverable")
    ap.add_argument("path")
    ap.add_argument("--mode", choices=("a", "b"), default=None)
    ap.add_argument("--slides", type=int, default=0)
    ap.add_argument("--figures-dir", default=None)
    ap.add_argument("--allow-text-only", action="store_true")
    ap.add_argument("--scope", choices=("full", "partial"), default="full")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.path):
        print(f"ERROR: file not found: {args.path}", file=sys.stderr)
        return 2
    try:
        with open(args.path, encoding="utf-8") as f:
            text = f.read()
    except OSError as exc:
        print(f"ERROR: cannot read {args.path}: {exc}", file=sys.stderr)
        return 2

    mode = args.mode or detect_mode(text)
    if not mode:
        print("ERROR: cannot tell Mode A from Mode B; pass --mode a|b", file=sys.stderr)
        return 2

    checks = []
    if mode == "a":
        verify_mode_a(args.path, text, checks, args)
    else:
        verify_mode_b(args.path, text, checks, args)

    failed = [c for c in checks if not c[1]]
    if args.json:
        print(json.dumps({
            "ok": not failed,
            "mode": mode,
            "file": os.path.abspath(args.path),
            "checks": [{"name": n, "ok": o, "detail": d} for n, o, d in checks],
            "failed": [n for n, _, _ in failed],
        }, ensure_ascii=False, indent=2))
    else:
        print(f"verify_output: {args.path} (mode {mode})")
        print("-" * 70)
        for name, ok, detail in checks:
            print(("PASS " if ok else "FAIL ") + name + (f" :: {detail}" if detail else ""))
        print("-" * 70)
        if failed:
            print(f"FAILED {len(failed)} of {len(checks)} check(s)")
            if any(n.startswith("A3") for n, _, _ in failed):
                print("Mode A needs original slide images. Render them first:")
                print("  run.py render_pptx_pages <deck.pptx> --prefix <L> --figures <dir>/figures")
                print("A text-only handout is only acceptable with --allow-text-only and explicit user consent.")
        else:
            print(f"OK: {len(checks)} check(s) passed")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
