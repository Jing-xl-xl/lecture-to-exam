#!/usr/bin/env python3
"""Extract audio from a Zoom recording link via yt-dlp. No personal paths.

Usage:
    python3 scripts/zoom_fetch.py "<zoom-url>" -o "<output.m4a>" [options]

Options:
    -o, --output        Output .m4a path (default: ./<title>.m4a)
    --cookies-from-browser NAME   e.g. chrome / safari, for SSO-gated links
    --cookies FILE      Netscape cookie file (alternative to browser cookies)
    --ffmpeg-location PATH        pass to yt-dlp if ffmpeg is not on PATH
    --simulate          Only probe formats, do not download
    --yt-dlp PATH       yt-dlp executable (default: YTDLP_BIN env or auto-detect)

Output is always audio-only m4a. The script is a thin wrapper around yt-dlp;
it does not bundle or modify yt-dlp (which is MIT licensed).
"""
import os
import sys
import shutil
import argparse
import subprocess


def build_cmd(args):
    exe = args.yt_dlp or os.environ.get("YTDLP_BIN") or shutil.which("yt-dlp")
    if not exe:
        raise SystemExit("ERROR: yt-dlp not found. Install: pip install yt-dlp (or set YTDLP_BIN)")

    out = args.output
    if out and os.path.isdir(out):
        out = os.path.join(out, "%(title)s.%(ext)s")
    template = out or os.path.join(os.getcwd(), "%(title)s.%(ext)s")
    if not template.lower().endswith((".m4a", "%(ext)s")):
        template = os.path.splitext(template)[0] + ".m4a"

    cmd = [
        exe,
        "-f", "ba",                       # best audio only
        "-x",                             # extract audio
        "--audio-format", "m4a",
        "-o", template,
        "--no-playlist",
    ]
    if args.simulate:
        cmd = [exe, "--simulate", "--list-formats"]
    else:
        if args.cookies_from_browser:
            cmd += ["--cookies-from-browser", args.cookies_from_browser]
        if args.cookies:
            cmd += ["--cookies", args.cookies]
        if args.ffmpeg_location:
            cmd += ["--ffmpeg-location", args.ffmpeg_location]
    cmd.append(args.url)
    return cmd, template


def main():
    ap = argparse.ArgumentParser(description="Extract m4a audio from a Zoom recording link")
    ap.add_argument("url", help="Zoom recording share/play URL")
    ap.add_argument("-o", "--output", help="Output .m4a path or directory")
    ap.add_argument("--cookies-from-browser", help="Read SSO cookies from a browser store")
    ap.add_argument("--cookies", help="Netscape-format cookie file")
    ap.add_argument("--ffmpeg-location", help="Path to ffmpeg binary")
    ap.add_argument("--simulate", action="store_true", help="Probe formats only")
    ap.add_argument("--yt-dlp", help="yt-dlp executable path")
    args = ap.parse_args()

    cmd, template = build_cmd(args)
    print("Running:", " ".join(cmd), file=sys.stderr)
    rc = subprocess.call(cmd)
    if rc != 0:
        print(f"ERROR: yt-dlp exited with {rc}.", file=sys.stderr)
        print("If the link is SSO-gated, retry with --cookies-from-browser chrome (or safari).", file=sys.stderr)
        return rc
    if not args.simulate:
        print(f"Expected output: {template}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
