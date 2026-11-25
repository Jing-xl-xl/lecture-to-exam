#!/usr/bin/env python3
"""Suggest which slide decks a recording actually taught.

Decks are named by module (L5, L7a), recordings by date or session (S09, S10),
so the mapping is rarely obvious. This scores each deck against the transcript
using topic keyword families and prints a ranked table with a confidence.

It only suggests: a human still confirms before anything is written.

Usage:
    python3 scripts/match_decks.py --recording _转录稿_S10.md --decks ../6045lecture10
    python3 scripts/match_decks.py --recording a.md --recording b.md --decks *.pptx

Exit: 0 ok | 2 bad input
"""
import os
import re
import sys
import glob
import math
import zipfile
import argparse

FAMILIES = {
    "firewall": r"firewall|packet filter|iptables|access control list|DMZ|proxy|UTM|rule table",
    "tunnelling": r"tunnel|VPN|IPsec|authentication header|\bAH\b|\bESP\b|security association",
    "ids": r"intrusion|\bIDS\b|\bIPS\b|signature|anomaly|false positive|base rate|alarm",
    "tls": r"\bTLS\b|\bSSL\b|handshake|cipher suite|certificate|HTTPS",
    "web": r"cookie|same origin|\bSOP\b|\bXSS\b|CSRF|SQL injection|\bDOM\b",
    "crypto": r"RSA|AES|hash|key exchange|modular|diffie",
    "auth": r"authentication|password|biometric|two-factor|2FA",
    "pki": r"\bPKI\b|certificate authority|\bCRL\b|trust chain|digital signature",
}


MAX_UNCOMPRESSED = 200 * 1024 * 1024  # a slide deck is megabytes, never this big


def deck_text(path):
    """Slide text from a .pptx (zip + runs), order-insensitive for scoring.

    The size cap keeps a malicious/corrupt zip (zip bomb) from exhausting RAM.
    """
    try:
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
            chunks = []
            total = 0
            for n in names:
                raw = z.read(n)
                total += len(raw)
                if total > MAX_UNCOMPRESSED:
                    print(f"WARN: {os.path.basename(path)} decompresses past the cap; "
                          f"scoring only the first {len(chunks)} slides", file=sys.stderr)
                    break
                chunks += re.findall(r"<a:t\b[^>]*>(.*?)</a:t>", raw.decode("utf-8", "ignore"), re.S)
            return " ".join(chunks), len(names)
    except Exception:
        return "", 0


def vector(text):
    low = text.lower()
    return {k: len(re.findall(p, low, re.I)) for k, p in FAMILIES.items()}


def cosine(a, b):
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def main():
    ap = argparse.ArgumentParser(description="Suggest deck <-> recording matches")
    ap.add_argument("--recording", action="append", required=True, help="transcript .md (repeatable)")
    ap.add_argument("--decks", nargs="+", required=True, help=".pptx files or directories")
    args = ap.parse_args()

    decks = []
    for item in args.decks:
        if os.path.isdir(item):
            decks += sorted(glob.glob(os.path.join(item, "*.pptx")))
        elif os.path.isfile(item):
            decks.append(item)
    if not decks:
        print("ERROR: no .pptx found", file=sys.stderr)
        return 2

    deck_vecs = {}
    for d in decks:
        text, pages = deck_text(d)
        deck_vecs[d] = (vector(text), pages)

    for rec in args.recording:
        if not os.path.isfile(rec):
            print(f"ERROR: recording not found: {rec}", file=sys.stderr)
            return 2
        with open(rec, encoding="utf-8") as f:
            body = f.read()
        rv = vector(body)
        top = sorted(((cosine(rv, dv), d, pages) for d, (dv, pages) in deck_vecs.items()),
                     reverse=True)
        print(f"\n=== {os.path.basename(rec)} ===")
        print(f"{'score':>6}  {'pages':>5}  deck")
        for score, path, pages in top:
            flag = "  <-- likely taught" if score >= 0.75 else ("  (weak)" if score < 0.35 else "")
            print(f"{score:6.2f}  {pages:5d}  {os.path.basename(path)}{flag}")
        best = top[0]
        print(f"\n建议：{os.path.basename(best[1])}（{best[0]:.2f}）。"
              f"低于 0.35 的 deck 视为本讲未讲；仍需人工确认后再写讲义。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
