#!/usr/bin/env python3
"""Host-agnostic environment helpers shared by run.py and check_env.py.

Nothing in here hardcodes a particular agent host, user name, or install path.
Every candidate is either an environment variable, derived from this file's own
location, or a conventional location for the current platform.

No third-party imports: this module must import cleanly under any Python 3.8+.
"""
import os
import re
import sys
import json
import shutil
import subprocess

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")


# --------------------------------------------------------------------------- #
# platform
# --------------------------------------------------------------------------- #
def is_macos():
    return sys.platform == "darwin"


def is_windows():
    return os.name == "nt"


def is_linux():
    return sys.platform.startswith("linux")


def platform_name():
    if is_macos():
        return "macos"
    if is_windows():
        return "windows"
    if is_linux():
        return "linux"
    return sys.platform


def run(cmd, timeout=30, cwd=None):
    """Run a probe command. Never raises; returns (ok, output)."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, cwd=cwd)
        return p.returncode == 0, (p.stdout + p.stderr).strip()
    except Exception as exc:  # noqa: BLE001 - probes must never crash the caller
        return False, str(exc)


def which(name):
    return shutil.which(name) if name else None


def _existing(paths):
    out = []
    for p in paths:
        if p and p not in out and os.path.exists(p):
            out.append(p)
    return out


# --------------------------------------------------------------------------- #
# Python
# --------------------------------------------------------------------------- #
def python_candidates():
    """Interpreters worth probing, most specific first.

    PYTHON_BIN wins; then the interpreter running us; then a project venv next
    to the skill; then whatever PATH offers.
    """
    venv = [
        os.path.join(SKILL_ROOT, ".venv", "bin", "python"),
        os.path.join(SKILL_ROOT, ".venv", "Scripts", "python.exe"),
        os.path.join(SKILL_ROOT, "venv", "bin", "python"),
    ]
    return _existing([
        os.environ.get("PYTHON_BIN"),
        sys.executable,
        *venv,
        which("python3"),
        which("python"),
        which("py"),
    ])


def probe_modules(py, modules):
    """True if `py` can import every module in `modules`."""
    if not modules:
        return True, "no extra modules required"
    probe = (
        "import importlib, sys\n"
        "for n in " + repr(list(modules)) + ":\n"
        "    mod = 'pymupdf' if n == 'pymupdf' else n\n"
        "    try:\n"
        "        m = importlib.import_module(mod)\n"
        "    except ImportError:\n"
        "        if mod == 'pymupdf':\n"
        "            try:\n"
        "                m = importlib.import_module('fitz')\n"
        "            except ImportError:\n"
        "                sys.exit(1)\n"
        "        else:\n"
        "            sys.exit(1)\n"
        "    print(getattr(m, '__version__', 'ok'))\n"
        "sys.exit(0)\n"
    )
    ok, out = run([py, "-c", probe])
    version = out.splitlines()[-1] if (ok and out) else "missing"
    return ok, version


def resolve_python(modules=(), verbose=False):
    """Pick the first interpreter that can import `modules`.

    Returns (path, detail). `path` is None when nothing qualifies.
    """
    failures = []
    for py in python_candidates():
        ok, detail = probe_modules(py, modules)
        if ok:
            return py, detail
        failures.append(f"{py}: {detail}" if verbose else py)
    return None, "; ".join(failures) if failures else "no python interpreter found"


# --------------------------------------------------------------------------- #
# Node
# --------------------------------------------------------------------------- #
def node_candidates():
    return _existing([
        os.environ.get("NODE_BIN"),
        which("node"),
        which("node.exe"),
    ])


def resolve_node():
    cands = node_candidates()
    return (cands[0] if cands else None)


def node_module_dirs():
    """Directories where a Node dependency may live, most local first."""
    home = os.path.expanduser("~")
    dirs = []
    for p in (os.environ.get("NODE_PATH") or "").split(os.pathsep):
        if p:
            dirs.append(p)
    dirs += [
        os.path.join(SKILL_ROOT, "node_modules"),
        os.path.join(os.getcwd(), "node_modules"),
        os.path.join(home, "node_modules"),
    ]
    # Global installs (npm root -g) are common for one-off host setups.
    npm = which("npm")
    if npm:
        ok, out = run([npm, "root", "-g"], timeout=20)
        if ok and out.strip():
            dirs.append(out.strip().splitlines()[-1])
    # npx scratch installs, e.g. ~/.npm/_npx/<hash>/node_modules
    npx_root = os.path.join(home, ".npm", "_npx")
    if os.path.isdir(npx_root):
        try:
            for d in sorted(os.listdir(npx_root)):
                dirs.append(os.path.join(npx_root, d, "node_modules"))
        except OSError:
            pass
    # De-duplicate while keeping order.
    seen, out = set(), []
    for d in dirs:
        if d and d not in seen:
            seen.add(d)
            out.append(d)
    return out


def resolve_node_module(node, module):
    """Return the resolved path of `module` as `node` would load it, or None."""
    if not node:
        return None
    dirs = node_module_dirs()
    script = (
        "const p=require('path');const c=" + json.dumps(dirs) + ";"
        "for(const x of c){try{console.log(require.resolve(p.join(x,'" + module + "')));"
        "process.exit(0)}catch(e){}}process.exit(1);"
    )
    ok, out = run([node, "-e", script], timeout=30)
    return out.splitlines()[-1] if (ok and out.strip()) else None


# --------------------------------------------------------------------------- #
# Browsers / Chromium
# --------------------------------------------------------------------------- #
def chromium_roots():
    home = os.path.expanduser("~")
    roots = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH")]
    if is_macos():
        roots.append(os.path.join(home, "Library", "Caches", "ms-playwright"))
    elif is_windows():
        roots.append(os.path.join(os.environ.get("LOCALAPPDATA", ""), "ms-playwright"))
        roots.append(os.path.join(home, "AppData", "Local", "ms-playwright"))
    roots.append(os.path.join(home, ".cache", "ms-playwright"))
    return _existing(roots)


def find_chromium():
    """Return (path, detail) for a cached Playwright Chromium build."""
    for root in chromium_roots():
        try:
            for name in sorted(os.listdir(root)):
                if name.startswith(("chromium", "chromium_headless")):
                    return True, os.path.join(root, name)
        except OSError:
            continue
    return False, "no Playwright Chromium cache (run: npx playwright install chromium)"


# --------------------------------------------------------------------------- #
# LibreOffice
# --------------------------------------------------------------------------- #
def soffice_candidates():
    cands = [os.environ.get("SOFFICE_BIN"), which("soffice"), which("libreoffice")]
    if is_macos():
        cands.append("/Applications/LibreOffice.app/Contents/MacOS/soffice")
        cands.append(os.path.expanduser("~/Applications/LibreOffice.app/Contents/MacOS/soffice"))
    if is_windows():
        for base in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                     os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")):
            cands.append(os.path.join(base, "LibreOffice", "program", "soffice.exe"))
    if is_macos():
        # A mounted DMG is the safest way to use a healthy copy without
        # touching /Applications (the installed one is often broken).
        cands += _mounted_dmg_soffice()
    return _existing(cands)


def _mounted_dmg_soffice():
    out = []
    try:
        for name in os.listdir("/Volumes"):
            app = os.path.join("/Volumes", name, "LibreOffice.app", "Contents", "MacOS", "soffice")
            if os.path.exists(app):
                out.append(app)
    except OSError:
        pass
    return out


def probe_soffice(path):
    """A LibreOffice that cannot start is worse than a missing one: verify it."""
    ok, out = run([path, "--headless", "--version"], timeout=60)
    first = out.splitlines()[0] if out else ""
    if ok and ("libreoffice" in out.lower() or "soffice" in out.lower()):
        return True, first
    return False, first or "soffice did not start"


# --------------------------------------------------------------------------- #
# Playwright browser resolution
# --------------------------------------------------------------------------- #
CHROMIUM_BIN_NAMES = {
    "chrome", "chrome.exe",
    "chrome-headless-shell", "chrome-headless-shell.exe",
    "Google Chrome for Testing",
}


def playwright_expectation(node, module_path, timeout=30):
    """Ask a resolved playwright module which Chromium it wants, and whether it exists.

    Returns (expected_path, exists). This is what `check_env` must report: a
    cached directory can exist while the pinned revision does not, and the
    difference is exactly what breaks PDF export.
    """
    if not node or not module_path:
        return None, False
    script = (
        "const pw=require(" + json.dumps(module_path) + ");"
        "const fs=require('fs');"
        "let p='';try{p=pw.chromium.executablePath()}catch(e){}"
        "console.log(JSON.stringify({path:p,exists:!!p&&fs.existsSync(p)}));"
    )
    ok, out = run([node, "-e", script], timeout=timeout)
    if not ok or not out.strip():
        return None, False
    try:
        data = json.loads(out.strip().splitlines()[-1])
    except ValueError:
        return None, False
    return data.get("path"), bool(data.get("exists"))


def cached_chromium_binaries(max_depth=4):
    """Every Chromium executable already present in a Playwright cache.

    html_to_pdf.js can launch one of these when the pinned revision is missing,
    which keeps PDF export working after a partial `playwright install`.
    """
    found = []
    for root in chromium_roots():
        root_depth = root.rstrip(os.sep).count(os.sep)
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath.count(os.sep) - root_depth >= max_depth:
                dirnames[:] = []
            for name in filenames:
                if name in CHROMIUM_BIN_NAMES:
                    found.append(os.path.join(dirpath, name))
    return found


def redact_url(url):
    """Hide the access token in a Zoom share URL before writing it to a log.

    A /rec/share/<token> link IS a credential: anyone holding it can watch the
    recording without signing in. Keep the host and path so the line is still
    useful, drop the token.
    """
    return re.sub(r"(/rec/(?:share|play)/)[^/?#\s]+", r"\1<redacted>", url or "")
