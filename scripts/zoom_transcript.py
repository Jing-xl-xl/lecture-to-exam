#!/usr/bin/env python3
"""Fetch Zoom's OFFICIAL cloud transcript for a /rec/share/ recording.

Zoom's unified player exposes a feature-config API. When the host enabled audio
transcription, that config declares a transcript getApi. This script:
  1. GET the share page -> extract __zm_unified_player__.featureConfigApi
     (falls back to the /nws/recording/2.0/share/<uuid>/feature-config pattern)
  2. GET featureConfigApi -> read result.transcript.status and getApi
  3. GET transcript getApi -> result.dataList (segments: startTime/endTime/text/userName),
     or fall back to captions.transcriptCaptionApi (WebVTT)
  4. Write a transcript Markdown following references/transcript-spec.md

WHY THIS FIRST: an official transcript is available in seconds, is accurate,
and already carries precise timestamps + speaker labels. This skill does NOT
transcribe audio itself. Exit codes:
  0 = transcript written
  3 = NO_TRANSCRIPT — the host did not enable the official transcript; the
      caller downloads the audio only and stops for the user to transcribe
      externally.
  1 = ERROR — access/network/API problem (password, expired, SSO, curl
      failure). This is NOT a missing transcript; fix access first.

Usage:
    python3 scripts/zoom_transcript.py "<share-url>" -o "_转录稿.md" \
        [--referer https://<tenant>/] [--with-speaker]

No personal paths and no tenant hardcoding: the domain and Referer are derived
from the share URL (overridable with --domain / --referer).
"""
import os
import re
import sys
import json
import shutil
import argparse
import subprocess
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402

CURL = shutil.which("curl") or "curl"


def fail(msg, code=1):
    """Print a clean error to stderr and exit with `code` (never a traceback)."""
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def no_transcript(msg):
    """Contract: exit 3 with a NO_TRANSCRIPT message = official transcript is
    not available (host did not enable it). Callers download audio and stop.
    Access problems (password / expired / SSO) must NOT use this — they exit 1
    with an ERROR message so they are not mistaken for a missing transcript."""
    fail(f"NO_TRANSCRIPT: {msg}", 3)


def curl_get(url, referer):
    p = subprocess.run([CURL, "-sL", "--max-time", "45", "-e", referer, url],
                       capture_output=True, text=True)
    if p.returncode != 0:
        fail(f"ERROR: curl failed ({p.returncode}) fetching {url}: {p.stderr.strip()[:200]}")
    return p.stdout


def get_json(url, referer):
    txt = curl_get(url, referer)
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        fail(f"ERROR: API did not return JSON. URL={url}\n{txt[:200]}")


def unescape_api(path):
    return path.replace("\\/", "/").replace("\\\u002F", "/")


def find_feature_config_api(html):
    """Prefer the exact featureConfigApi declared by the player, else rebuild it."""
    m = re.search(r'featureConfigApi\s*:\s*"([^"]+)"', html)
    if m:
        return unescape_api(m.group(1))
    m = re.search(r'/nws/recording/2\.0/share/([0-9A-Fa-f-]+)', html)
    if m:
        return f"/nws/recording/2.0/share/{m.group(1)}/feature-config?pageType=web"
    return None


def abs_url(host, path, domain_default="zoom.us"):
    if path.startswith("http://") or path.startswith("https://"):
        return path
    host = host or domain_default
    return f"https://{host}{path}"


def parse_ts_to_seconds(ts):
    s = str(ts).strip().replace(",", ".")
    parts = s.split(":")
    try:
        if len(parts) == 3:
            h, m, sec = int(parts[0]), int(parts[1]), float(parts[2])
        elif len(parts) == 2:
            h, m, sec = 0, int(parts[0]), float(parts[1])
        else:
            return 0.0
        return h * 3600 + m * 60 + sec
    except ValueError:
        return 0.0


def mmss(ts):
    total = int(parse_ts_to_seconds(ts))
    return f"{total // 60:02d}:{total % 60:02d}"


def segments_from_json(data_list, with_speaker):
    segs = []
    for it in data_list:
        text = (it.get("text") or "").strip()
        if not text:
            continue
        speaker = (it.get("userName") or "").strip()
        line = f"{speaker}: {text}" if (with_speaker and speaker) else text
        segs.append((it.get("startTime", "00:00:00"), line))
    return segs


def segments_from_vtt(vtt_text, with_speaker):
    """WEBVTT fallback: numbered cue / timing / text blocks."""
    out = []
    lines = [l.rstrip("\r") for l in vtt_text.splitlines()]
    i = 0
    while i < len(lines):
        if "-->" in lines[i]:
            timing = lines[i]
            start = timing.split("-->")[0].strip()
            body = []
            i += 1
            while i < len(lines) and lines[i].strip() and "-->" not in lines[i]:
                body.append(lines[i].strip())
                i += 1
            text = " ".join(body).strip()
            if text:
                if not with_speaker:
                    text = re.sub(r"^[^:]{1,60}:\s", "", text)
                out.append((start, text))
            continue
        i += 1
    return out


def detect_language(segments):
    """Rough zh/en/mixed guess from the segment text (CJK vs Latin letters)."""
    text = " ".join(t for _, t in segments)
    cjk = sum(1 for ch in text if "一" <= ch <= "鿿")
    latin = sum(1 for ch in text if ("a" <= ch.lower() <= "z"))
    if cjk == 0:
        return "en"
    if latin == 0 or cjk >= latin:
        return "zh"
    return "mixed"


def write_transcript(path, source_name, source, segments, language=None):
    language = language or detect_language(segments)
    lines = [
        f"# 转录稿 — {source_name}",
        "",
        f"- Transcript source: {source}",
        f"- Detected language: {language}",
        "- Note: official Zoom transcript; still verify technical terms against the original slides before citing.",
        "",
        "---",
        "",
    ]
    for ts, text in segments:
        lines.append(f"[{mmss(ts)}] {text}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return len(segments)


def fetch(url, out, domain, referer, with_speaker):
    print(f"fetching share page: {_common.redact_url(url)}", file=sys.stderr)
    html = curl_get(url, referer)
    fc_path = find_feature_config_api(html)
    if not fc_path:
        fail("ERROR: no feature-config API found in share page — the link may "
             "need a password, be expired, or require login. Open it in a "
             "browser first. This is NOT a missing-transcript case.")

    fc_url = abs_url(domain, fc_path)
    print(f"fetching feature-config: {fc_url}", file=sys.stderr)
    fc = get_json(fc_url, referer)
    if not fc.get("status"):
        fail(f"ERROR: feature-config API error: {fc.get('errorMessage')} "
             f"(access problem, not a missing transcript)")

    result = fc.get("result") or {}
    tr = result.get("transcript") or {}
    status = str(tr.get("status") or "").lower()
    if status != "success":
        no_transcript(f"official transcript status={status or 'absent'}")

    topic = (result.get("topic") or {}).get("value") or "Zoom recording"
    get_api = tr.get("getApi")
    segs = []
    source = "Zoom official cloud transcript"
    if get_api:
        print("fetching official transcript (getApi)", file=sys.stderr)
        td = get_json(abs_url(domain, get_api), referer)
        data_list = ((td.get("result") or {}).get("dataList")) or []
        segs = segments_from_json(data_list, with_speaker)
    if not segs:
        vtt_api = (result.get("captions") or {}).get("transcriptCaptionApi")
        if vtt_api:
            print("fetching official transcript (WebVTT)", file=sys.stderr)
            segs = segments_from_vtt(curl_get(abs_url(domain, vtt_api), referer), with_speaker)
            source = "Zoom official cloud transcript (VTT)"
    if not segs:
        no_transcript("transcript declared success but no segments returned")

    n = write_transcript(out, topic, source, segs)
    print(f"Wrote {out} ({n} segments)", file=sys.stderr)
    return {"out": out, "topic": topic, "segments": n, "source": source}


def main():
    ap = argparse.ArgumentParser(description="Fetch Zoom's official cloud transcript")
    ap.add_argument("url")
    ap.add_argument("-o", "--output", default="_转录稿.md")
    ap.add_argument("--domain", default=None, help="Zoom tenant domain (default: from URL)")
    ap.add_argument("--referer", default=None)
    ap.add_argument("--with-speaker", action="store_true", help="Prefix each line with speaker name")
    args = ap.parse_args()

    host = urlparse(args.url).netloc or ""
    domain = args.domain or host
    referer = args.referer or (f"https://{host}/" if host else "https://zoom.us/")
    result = fetch(args.url, args.output, domain, referer, args.with_speaker)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
