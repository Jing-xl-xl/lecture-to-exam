#!/usr/bin/env python3
"""Single entry point for every lecture-to-exam tool.

Why this exists: an agent's working directory is the user's project, not this
skill's directory. Hardcoded `python3 scripts/xxx.py` only works after a manual
`cd`, which is the most common way this skill broke on other hosts. run.py
resolves the skill root from its own location, picks an interpreter that can
actually import what the tool needs, and forwards argv unchanged.

Usage:
    python3 <skill>/scripts/run.py --list
    python3 <skill>/scripts/run.py <tool> [tool args...]

Examples:
    python3 "$SKILL_ROOT/scripts/run.py" check_env
    python3 "$SKILL_ROOT/scripts/run.py" md_to_html notes.md notes.html
    python3 "$SKILL_ROOT/scripts/run.py" html_to_pdf notes.html notes.pdf
    python3 "$SKILL_ROOT/scripts/run.py" verify_output notes.md --mode a

Exit codes: the tool's own exit code is passed through (documented in
SKILL.md). run.py itself exits 1 on a setup problem and 2 on bad usage.
"""
import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402


# tool -> (script filename, required python modules, required node modules)
TOOLS = {
    "check_env":            ("check_env.py", (), ()),
    "verify_output":        ("verify_output.py", (), ()),
    "validate_review_input": ("validate_review_input.py", (), ()),
    "zoom_transcript":      ("zoom_transcript.py", (), ()),
    "zoom_fetch":           ("zoom_fetch.py", (), ()),
    "zoom_fetch_share":     ("zoom_fetch_share.py", (), ()),
    "extract_pptx":         ("extract_pptx.py", (), ()),
    "extract_pdf":          ("extract_pdf.py", ("pymupdf",), ()),
    "render_pptx_pages":    ("render_pptx_pages.py", ("pymupdf",), ()),
    "md_to_html":           ("md_to_html.py", ("markdown",), ()),
    "html_to_pdf":          ("html_to_pdf.js", (), ("playwright",)),
}

DESCRIPTIONS = {
    "check_env": "read-only dependency check (--json for machines)",
    "verify_output": "gate a finished .md against its format spec",
    "validate_review_input": "enforce >= 2 lecture notes for review mode",
    "zoom_transcript": "fetch Zoom's official cloud transcript",
    "zoom_fetch": "download audio, old /rec/play/ links (yt-dlp)",
    "zoom_fetch_share": "download audio, new /rec/share/ links",
    "extract_pptx": "PPTX per-slide text (page accounting only)",
    "extract_pdf": "PDF text + rendered page PNGs (PyMuPDF)",
    "render_pptx_pages": "PPTX -> original slide PNGs (LibreOffice)",
    "md_to_html": "Markdown -> print-ready HTML",
    "html_to_pdf": "HTML -> self-contained A4 PDF (Playwright)",
}


def print_tools():
    print("lecture-to-exam tools")
    print("-" * 68)
    for name in sorted(TOOLS):
        _, py_req, node_req = TOOLS[name]
        need = [*py_req, *node_req] or ["stdlib"]
        print(f"  {name:22} requires: {', '.join(need)}")
        print(f"  {'':22} {DESCRIPTIONS[name]}")
    print("-" * 68)
    print("usage: run.py <tool> [args...]   e.g. run.py check_env --json")


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    return 1


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print_tools()
        return 0 if len(argv) > 1 else 2
    if argv[1] in ("-l", "--list", "list"):
        print_tools()
        return 0

    tool = argv[1]
    if tool not in TOOLS:
        return fail(f"unknown tool '{tool}'. Run: run.py --list")

    script, py_modules, node_modules = TOOLS[tool]
    script_path = os.path.join(_common.SCRIPTS_DIR, script)
    if not os.path.isfile(script_path):
        return fail(f"script missing from this install: {script_path}")

    if script.endswith(".js"):
        node = _common.resolve_node()
        if not node:
            return fail("node not found. Install Node.js 18+ (or set NODE_BIN).")
        if node_modules:
            missing = [m for m in node_modules
                       if not _common.resolve_node_module(node, m)]
            if missing:
                print(f"WARNING: node module(s) not resolved: {', '.join(missing)}",
                      file=sys.stderr)
                print("  The tool will print its own install hint.", file=sys.stderr)
        cmd = [node, script_path, *argv[2:]]
    else:
        py, detail = _common.resolve_python(py_modules, verbose=True)
        if not py:
            hint = " ".join(py_modules) or "the standard library"
            return fail(
                f"no Python interpreter can import {hint}.\n"
                f"  tried: {detail}\n"
                f"  fix: python3 -m pip install {' '.join(py_modules)}\n"
                f"  or:  PYTHON_BIN=/path/to/python python3 {os.path.abspath(__file__)} {tool} ..."
            )
        cmd = [py, script_path, *argv[2:]]

    try:
        return subprocess.run(cmd).returncode
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main(sys.argv))
