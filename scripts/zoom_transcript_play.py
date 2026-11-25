#!/usr/bin/env python3
"""Fetch Zoom's official transcript for an old-style /rec/play/ link.

Why this exists: Zoom's share page used to embed a feature-config object, which
zoom_transcript.py reads with curl. The current player is client-side: the HTML
is an app shell, and the transcript is fetched separately as WebVTT. Reading it
therefore needs a real browser AND the session of a signed-in user (recordings
are usually restricted to meeting participants).

Fast path when possible: use zoom_transcript.py (no browser needed). This script
is the fallback, and it is what the dispatcher picks for /rec/play/ URLs.

Usage:
    python3 scripts/zoom_transcript_play.py "<play-url>" -o "_转录稿.md" \
        [--from-browser chrome] [--wait 25] [--domain hku.zoom.us]

Exit codes (same contract as zoom_transcript.py):
    0  transcript written
    3  NO_TRANSCRIPT — page opened, no transcript track (host did not enable it)
    1  ERROR — access problem (login/password/SSO) or missing dependency

Privacy: browser cookies are read into memory, written to a per-run temp file
only so the Node helper can use them, and deleted on exit. Cookie values are
never printed. URLs are redacted before logging.
"""
import os
import sys
import json
import shutil
import argparse
import tempfile
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402
import zoom_transcript as zt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SNIFFER = os.path.join(HERE, "_sniff_vtt.js")


def fail(msg, code=1):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def read_cookies(browser):
    """Return Playwright-shaped cookies for *.zoom.us, or [] on failure."""
    try:
        import browser_cookie3
    except ImportError:
        fail("ERROR: dependency missing: browser_cookie3\n"
             "  fix: python3 -m pip install browser_cookie3\n"
             "  (needed to reuse the Zoom session of a browser you are already signed in to)")
    try:
        jar = getattr(browser_cookie3, browser)()
    except Exception as exc:  # noqa: BLE001 - browser stores are all different
        fail(f"ERROR: cannot read cookies from {browser}: {type(exc).__name__}: {exc}\n"
             f"  Check that {browser} is installed and that you have signed in to the Zoom tenant.")
    out = []
    for c in jar:
        if "zoom.us" not in (c.domain or ""):
            continue
        out.append({
            "name": c.name,
            "value": c.value,
            "domain": c.domain,
            "path": c.path or "/",
            "expires": int(c.expires) if c.expires else -1,
            "secure": bool(c.secure),
            "httpOnly": False,
        })
    return out


def main():
    ap = argparse.ArgumentParser(description="Transcript for /rec/play/ links (browser + VTT)")
    ap.add_argument("url")
    ap.add_argument("-o", "--output", default="_转录稿.md")
    ap.add_argument("--from-browser", default="chrome",
                    help="browser to borrow the Zoom session from (chrome/safari/edge/firefox)")
    ap.add_argument("--wait", type=int, default=25, help="seconds to wait for the transcript track")
    ap.add_argument("--domain", default=None, help="unused; kept for CLI symmetry")
    args = ap.parse_args()

    node = _common.resolve_node()
    if not node:
        fail("ERROR: node not found (needed to drive a browser).")
    if not os.path.isfile(SNIFFER):
        fail(f"ERROR: helper missing: {SNIFFER}")

    print(f"opening player with a {args.from_browser} session: {_common.redact_url(args.url)}",
          file=sys.stderr)
    cookies = read_cookies(args.from_browser)
    if not cookies:
        fail("ERROR: no *.zoom.us cookies found in " + args.from_browser +
             ".\n  Sign in to the Zoom tenant in that browser first, then retry.")

    run_dir = tempfile.mkdtemp(prefix="zoomplay_")
    cookie_file = os.path.join(run_dir, "cookies.json")
    result_file = os.path.join(run_dir, "capture.json")
    try:
        with open(cookie_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f)
        proc = subprocess.run(
            [node, SNIFFER, args.url, cookie_file, result_file, str(max(5, args.wait) * 1000)],
            capture_output=True, text=True,
        )
        if proc.stderr.strip():
            print(proc.stderr.strip(), file=sys.stderr)
        if not os.path.exists(result_file):
            fail("ERROR: browser helper produced no result (dependency or launch failure).")
        with open(result_file, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("error"):
            fail("ERROR: " + str(data["error"])[:400])

        vtt = data.get("vtt") or ""
        if not vtt.strip():
            fail("NO_TRANSCRIPT: the player opened but no transcript track was found.\n"
                 "  The host may not have enabled audio transcription for this recording.",
                 3)

        segs = zt.segments_from_vtt(vtt, with_speaker=True)
        if not segs:
            fail("NO_TRANSCRIPT: the transcript track was empty.", 3)

        topic = (data.get("title") or "Zoom recording").split(" - Zoom")[0].strip()
        n = zt.write_transcript(args.output, topic,
                                "Zoom official cloud transcript (player VTT)", segs)
        print(f"Wrote {args.output} ({n} segments)", file=sys.stderr)
        print(json.dumps({"out": args.output, "topic": topic, "segments": n,
                          "source": "Zoom official cloud transcript (player VTT)"},
                         ensure_ascii=False))
        return 0
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
