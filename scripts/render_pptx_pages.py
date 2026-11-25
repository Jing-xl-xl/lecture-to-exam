#!/usr/bin/env python3
"""Render every page of a PPTX deck to PNG via LibreOffice, with no install.

On a Mac without LibreOffice installed system-wide, this script locates a
LibreOffice.app (from a mounted DMG or an installed app), mounts a DMG if
given, converts the deck to PDF headlessly, then renders pages to PNG via
PyMuPDF. All paths are arguments — nothing is hardcoded.

Usage:
    python3 scripts/render_pptx_pages.py deck.pptx --prefix C --figures ./figures \
        [--lo-app /path/to/LibreOffice.app] [--dmg /path/to/LibreOffice.dmg] [--dpi 130]

If neither --lo-app nor --dmg is given, `soffice` on PATH is used. Blank slides
are still rendered; the agent decides in the Markdown whether to embed them.
"""
import os
import re
import sys
import shutil
import argparse
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402

CONVERT = r'''
import json, sys, os
try:
    import pymupdf as fitz
except ImportError:
    import fitz
pdf, prefix, figures, dpi = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
doc = fitz.open(pdf)
n = 0
for i, page in enumerate(doc, 1):
    pix = page.get_pixmap(dpi=dpi)
    pix.save(os.path.join(figures, f"{prefix}_p{i:02d}.png"))
    n += 1
print(json.dumps({"count": n}))
'''


def soffice_bin(lo_app, dmg, mountpoint):
    """Locate a soffice that actually starts. --dmg mounting is macOS-only."""
    if lo_app:
        exe = os.path.join(lo_app, "program", "soffice.exe") if os.name == "nt" \
            else os.path.join(lo_app, "Contents", "MacOS", "soffice")
        if not os.path.exists(exe):
            raise SystemExit(f"ERROR: no soffice inside {lo_app}")
        return exe, None
    if dmg:
        if sys.platform != "darwin":
            raise SystemExit(
                "ERROR: --dmg mounting is macOS-only. Install LibreOffice, pass --lo-app, "
                "or convert the deck to PDF yourself and use extract_pdf.py instead.")
        os.makedirs(mountpoint, exist_ok=True)
        subprocess.check_call(["hdiutil", "attach", "-nobrowse", "-mountpoint", mountpoint, dmg],
                              stdout=subprocess.DEVNULL)
        matches = []
        for root, dirs, files in os.walk(mountpoint):
            for d in dirs:
                if d == "LibreOffice.app":
                    matches.append(os.path.join(root, d))
                    dirs[:] = []
        if not matches:
            raise SystemExit("ERROR: LibreOffice.app not found in DMG")
        app = matches[0]
        subprocess.call(["xattr", "-dr", "com.apple.quarantine", app])
        return os.path.join(app, "Contents", "MacOS", "soffice"), mountpoint
    failures = []
    for cand in _common.soffice_candidates():
        fits, why = _common.probe_soffice(cand)
        if fits:
            return cand, None
        failures.append(f"{cand} ({why})")
    detail = "; ".join(failures) if failures else "none found"
    raise SystemExit(
        "ERROR: no working LibreOffice. Tried: " + detail + "\n"
        "  fix: install LibreOffice, pass --lo-app <app dir>, pass --dmg <dmg> (macOS), "
        "or convert the deck to PDF and use extract_pdf.py.")


def safe_prefix(prefix):
    """A page prefix becomes a filename; keep it to letters/digits/_/- only."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "", prefix or "")
    return cleaned or "S"


def main():
    ap = argparse.ArgumentParser(description="Render PPTX pages to PNG")
    ap.add_argument("pptx")
    ap.add_argument("--prefix", default="S")
    ap.add_argument("--figures")
    ap.add_argument("--dpi", type=int, default=130)
    ap.add_argument("--lo-app")
    ap.add_argument("--dmg")
    ap.add_argument("--python")
    args = ap.parse_args()
    args.prefix = safe_prefix(args.prefix)

    if not os.path.isfile(args.pptx):
        raise SystemExit(f"ERROR: pptx not found: {args.pptx}")
    figures = args.figures or os.path.join(os.path.dirname(os.path.abspath(args.pptx)), "figures")
    os.makedirs(figures, exist_ok=True)

    mountpoint = tempfile.mkdtemp(prefix="lo_mount_")
    tmpdir = tempfile.mkdtemp(prefix="lo_pdf_")
    # Isolate the LibreOffice user profile: a broken/partial system install can
    # leave a corrupt default profile that makes even a healthy soffice binary
    # fail with DeploymentException on --convert-to. A fresh profile avoids it.
    profile = tempfile.mkdtemp(prefix="lo_profile_")
    exe, mounted = soffice_bin(args.lo_app, args.dmg, mountpoint)
    try:
        subprocess.check_call([
            exe, f"-env:UserInstallation=file://{profile}",
            "--headless", "--convert-to", "pdf", "--outdir", tmpdir, args.pptx
        ], stdout=subprocess.DEVNULL)
        pdfs = [f for f in os.listdir(tmpdir) if f.lower().endswith(".pdf")]
        if not pdfs:
            raise SystemExit("ERROR: LibreOffice produced no PDF")
        pdf = os.path.join(tmpdir, pdfs[0])

        py = args.python or os.environ.get("PYTHON_BIN") or sys.executable
        import json
        fd, worker = tempfile.mkstemp(suffix=".py")
        os.close(fd)
        try:
            with open(worker, "w", encoding="utf-8") as f:
                f.write(CONVERT)
            proc = subprocess.run([py, worker, pdf, args.prefix, figures, str(args.dpi)],
                                  capture_output=True, text=True)
            if proc.returncode != 0:
                print(proc.stderr, file=sys.stderr)
                raise SystemExit("ERROR: page render failed. Install: pip install pymupdf")
            raw = proc.stdout
            brace = raw.find("{")
            data = json.loads(raw[brace:] if brace >= 0 else raw)
        finally:
            try:
                os.remove(worker)
            except OSError:
                pass
        print(f"Rendered {data['count']} slides to {figures} (prefix {args.prefix}, {args.dpi} dpi)")
    finally:
        if mounted:
            subprocess.call(["hdiutil", "detach", mounted, "-quiet"])
        import shutil as _sh
        for d in (profile, tmpdir, mountpoint):
            _sh.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    main()
