#!/usr/bin/env python3
"""Fetch a modern Zoom /rec/share/ recording (new unified player).

yt-dlp's Zoom extractor fails on the new player because the page no longer
embeds window.__data__; playback info lives behind an API. This script:
  1. GET the share page -> extract the playInfoApi UUID
  2. GET https://<tenant>/nws/recording/2.0/share/<uuid>?pageType=web
  3. read result.mediaInfo.playUrl (a signed mp4 URL)
  4. curl the signed URL WITH a Referer header (required, else HTTP 403)
  5. ffmpeg copy the audio track to m4a

No personal paths and no tenant hardcoding: the domain and Referer are derived
from the share URL and are overridable with --domain / --referer.

Usage:
    python3 scripts/zoom_fetch_share.py "<share-url>" -o "<out.m4a>" \
        [--domain <tenant>] [--referer https://<tenant>/] [--workdir DIR]

Set FFMPEG_BIN to point at a specific ffmpeg if it is not on PATH. Scratch
files (including the downloaded video) live in a unique temp dir and are
removed on exit.

Use this when zoom_fetch.py (yt-dlp) fails with "Unable to extract data".
"""
import os
import re
import sys
import json
import shutil
import argparse
import tempfile
import subprocess
from urllib.parse import urlparse

CURL = shutil.which("curl") or "curl"


def ffmpeg_bin():
    env = os.environ.get("FFMPEG_BIN")
    return (env if env and os.path.exists(env) else shutil.which(env) if env else None) \
        or shutil.which("ffmpeg") or "ffmpeg"


def run(cmd, capture=False):
    kw = {"check": True, "text": True}
    if capture:
        kw["stdout"] = subprocess.PIPE
        kw["stderr"] = subprocess.PIPE
    return subprocess.run(cmd, **kw)


def fetch(url, out, domain, referer, workdir=None):
    parent = workdir or tempfile.gettempdir()
    # Unique per-run scratch dir: parallel/large downloads must not share
    # filenames, and the extracted video (hundreds of MB) is removed on exit.
    rundir = tempfile.mkdtemp(prefix="zshare_", dir=parent)
    cookie = os.path.join(rundir, "cookies.txt")
    page = os.path.join(rundir, "share.html")
    info = os.path.join(rundir, "playinfo.json")
    tmp_mp4 = os.path.join(rundir, "video.mp4")
    try:
        print(f"fetching share page: {url}", file=sys.stderr)
        run([CURL, "-sL", "--max-time", "40", "-c", cookie, url, "-o", page])
        html = open(page, encoding="utf-8", errors="ignore").read()
        m = re.search(r"/nws/recording/2\.0/share/([0-9A-Fa-f-]+)", html)
        if not m:
            raise SystemExit("ERROR: no playInfoApi UUID found; this share link may need a password or be expired")
        uuid = m.group(1)

        api = f"https://{domain}/nws/recording/2.0/share/{uuid}?pageType=web"
        print(f"fetching play info ({uuid})", file=sys.stderr)
        run([CURL, "-s", "--max-time", "40", "-b", cookie, "-e", referer,
             "-H", "Accept: application/json", api, "-o", info])
        d = json.load(open(info, encoding="utf-8"))
        if not d.get("status"):
            raise SystemExit(f"ERROR: play info API error: {d.get('errorMessage')}")
        mi = (d.get("result") or {}).get("mediaInfo")
        if not mi or not mi.get("playUrl"):
            raise SystemExit("ERROR: play info API returned no mediaInfo.playUrl")
        print(f"topic={mi.get('mediaTopic')!r} duration={mi.get('mediaDuration')}s", file=sys.stderr)

        play_url = mi["playUrl"]
        print("downloading mp4 (signed URL, may take a while)", file=sys.stderr)
        run([CURL, "-sL", "-b", cookie, "-e", referer, "--max-time", "3600",
             play_url, "-o", tmp_mp4])
        if os.path.getsize(tmp_mp4) < 1000:
            raise SystemExit("ERROR: mp4 download failed (file empty or tiny). Check the Referer header and link validity.")

        print("extracting audio track to m4a", file=sys.stderr)
        ff = ffmpeg_bin()
        try:
            run([ff, "-y", "-i", tmp_mp4, "-vn", "-c:a", "copy", out], capture=True)
        except FileNotFoundError:
            raise SystemExit("ERROR: ffmpeg not found. Install ffmpeg (or set FFMPEG_BIN).")
        print(f"Wrote {out}", file=sys.stderr)
        return {"out": out, "topic": mi.get("mediaTopic"), "duration": mi.get("mediaDuration")}
    finally:
        shutil.rmtree(rundir, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Download audio from a modern Zoom share link")
    ap.add_argument("url")
    ap.add_argument("-o", "--output", default="recording.m4a")
    ap.add_argument("--domain", default=None, help="Zoom tenant domain (default: from URL)")
    ap.add_argument("--referer", default=None)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    host = urlparse(args.url).netloc
    domain = args.domain or (host if host and host != "zoom.us" else "zoom.us")
    referer = args.referer or (f"https://{host}/" if host else "https://zoom.us/")
    try:
        result = fetch(args.url, args.output, domain, referer, args.workdir or tempfile.gettempdir())
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"ERROR: {os.path.basename(str(e.cmd[0]))} failed (exit {e.returncode})")
    except json.JSONDecodeError:
        raise SystemExit("ERROR: play info API did not return JSON (link may need a password or be expired)")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
