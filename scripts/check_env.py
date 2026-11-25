#!/usr/bin/env python3
"""Read-only dependency check for lecture-to-exam.

Never installs anything. Reports OK / MISS / WARN, says which stage each
dependency serves, and prints copy-pasteable fixes. Every path is detected: no
host and no user path is hardcoded.

Usage:
    python3 <skill>/scripts/run.py check_env
    python3 <skill>/scripts/run.py check_env --json

Exit codes: 0 = every required dependency present, 1 = something required is
missing. WARN items never fail the check (conditional tools only).

Environment overrides: PYTHON_BIN, NODE_BIN, YTDLP_BIN, FFMPEG_BIN, SOFFICE_BIN,
PLAYWRIGHT_BROWSERS_PATH, NODE_PATH.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402

# Stage labels, so an agent can install only what the current task needs.
SERVES = {
    "python": "all Python tools",
    "curl": "A1 transcript, A2 audio download",
    "node": "A3 pdf, B pdf",
    "markdown": "A3/B md->html",
    "pymupdf": "A2 pdf/pptx extraction + rendering",
    "playwright": "A3/B html->pdf",
    "chromium": "A3/B html->pdf",
    "yt-dlp": "A1 audio download (only when no official transcript)",
    "ffmpeg": "A1 audio download (only when no official transcript)",
    "libreoffice": "A2 PPTX original slide images",
    "browser_cookie3": "A1 transcript for /rec/play/ links (borrow a browser session)",
}

STAGE_SETS = {
    "transcript (A1, share)": ["curl"],
    "transcript (A1, /rec/play/)": ["curl", "playwright", "chromium", "browser_cookie3"],
    "lecture notes (A2)": ["python", "curl", "markdown", "pymupdf", "libreoffice"],
    "pdf export (A3/B)": ["markdown", "playwright", "chromium"],
    "audio fallback": ["curl", "yt-dlp", "ffmpeg"],
}


def main():
    as_json = "--json" in sys.argv
    platform = _common.platform_name()
    results = []  # (kind, name, ok, detail, serves)

    def add(kind, name, ok, detail):
        results.append((kind, name, ok, detail, SERVES.get(name, "")))

    # Interpreter that actually runs the Python tools.
    py, _ = _common.resolve_python(())
    py_ver = ""
    if py:
        ok, out = _common.run([py, "--version"])
        py_ver = out.strip().replace("Python ", "") if ok else ""
    add("binary", "python",
        bool(py),
        (f"{py_ver} ({py})" if py else "no python3 on PATH"))

    curl = _common.which("curl")
    add("binary", "curl", bool(curl), curl or "not found")

    node = _common.resolve_node()
    node_ver = ""
    if node:
        ok, out = _common.run([node, "--version"])
        node_ver = out.strip() if ok else ""
    add("binary", "node", bool(node),
        f"{node_ver} ({node})".strip() if node else "not found (install Node.js 18+)")

    for name, env in (("yt-dlp", "YTDLP_BIN"), ("ffmpeg", "FFMPEG_BIN")):
        path = os.environ.get(env) or _common.which(name)
        add("conditional", name, bool(path),
            path or "not found (only needed to download audio when a recording has no official transcript)")

    for mod in ("markdown", "pymupdf"):
        pyx, detail = _common.resolve_python((mod,))
        add("python module", mod, bool(pyx),
            f"{detail} ({pyx})" if pyx else "missing in every candidate interpreter")

    pw = _common.resolve_node_module(node, "playwright") if node else None
    add("node module", "playwright", bool(pw), pw or "not found (npm install)")

    # A cached directory is not enough: the resolved Playwright pins a specific
    # Chromium revision, and a partial `playwright install` leaves that missing.
    if pw:
        expected, exists = _common.playwright_expectation(node, pw)
        if exists:
            add("browser", "chromium", True, expected)
        else:
            fallbacks = _common.cached_chromium_binaries()
            add("browser", "chromium", bool(fallbacks),
                (f"pinned revision missing ({expected}); html_to_pdf will fall back to "
                 f"{fallbacks[0]}") if fallbacks
                else f"expected {expected} — run: npx playwright install chromium")
    else:
        add("browser", "chromium", False, "playwright unresolved, cannot verify Chromium")

    # Old-style /rec/play/ links need a real browser plus a signed-in session.
    try:
        import browser_cookie3  # noqa: F401
        cookie_ok, cookie_detail = True, "importable"
    except ImportError:
        cookie_ok, cookie_detail = False, "not installed (pip install browser_cookie3)"
    add("conditional", "browser_cookie3", cookie_ok, cookie_detail)

    # LibreOffice: a binary that exists but cannot start is a failure, not a pass.
    soffice = None
    lo_detail = "not found (install LibreOffice, or pass --lo-app / --dmg)"
    for cand in _common.soffice_candidates():
        fits, why = _common.probe_soffice(cand)
        if fits:
            soffice, lo_detail = cand, f"{why} ({cand})"
            break
        lo_detail = f"found but failed to start: {why} ({cand})"
    add("renderer", "libreoffice", bool(soffice), lo_detail)

    warn_kinds = ("conditional", "renderer")
    missing = [(n, d) for k, n, o, d, _ in results if not o and k not in warn_kinds]
    warnings = [(n, d) for k, n, o, d, _ in results if not o and k in warn_kinds]
    missing_names = {n for n, _ in missing}

    if as_json:
        print(json.dumps({
            "ok": not missing,
            "platform": platform,
            "items": [{"kind": k, "name": n, "ok": o, "detail": d, "serves": s}
                      for k, n, o, d, s in results],
            "missing": sorted(missing_names),
            "warnings": [{"name": n, "detail": d} for n, d in warnings],
            "stages": STAGE_SETS,
        }, ensure_ascii=False, indent=2))
        return 0 if not missing else 1

    print(f"lecture-to-exam environment check  [{platform}]")
    print("-" * 78)
    for kind, name, ok, detail, serves in results:
        mark = "WARN" if (kind in warn_kinds and not ok) else ("OK  " if ok else "MISS")
        print(f"[{mark}] {name:12} {detail}")
        if serves:
            print(f"       {'':12} serves: {serves}")
    print("-" * 78)

    for label, deps in STAGE_SETS.items():
        bad = [d for d in deps if any(n == d and not o for _, n, o, _, _ in results)]
        state = "ok" if not bad else "needs " + ", ".join(bad)
        print(f"  {label:22} {state}")
    print("-" * 78)

    if missing:
        names = missing_names
        print("Missing required dependencies. Copy-paste, then re-run:")
        print()
        py_pkgs = [m for m in ("markdown", "pymupdf") if m in names]
        if py_pkgs:
            print("  # Python packages (install into the interpreter that runs this skill)")
            print(f"  {sys.executable} -m pip install " + " ".join(py_pkgs))
            print()
        if "curl" in names:
            print("  # curl")
            print("  # macOS: brew install curl   |   Linux: sudo apt install curl   |   Windows: use Git Bash")
            print()
        if names & {"playwright", "chromium", "node"}:
            print("  # Node / PDF rendering")
            print(f"  cd \"{_common.SKILL_ROOT}\" && npm install")
            print("  npx playwright install chromium")
            print()
        print("If a tool is installed but not detected, set PYTHON_BIN / NODE_BIN /")
        print("YTDLP_BIN / FFMPEG_BIN / SOFFICE_BIN / NODE_PATH to its path.")
        return 1

    print("All required dependencies are available.")
    if warnings:
        print("WARN items are conditional: install them when the matching stage is used.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
