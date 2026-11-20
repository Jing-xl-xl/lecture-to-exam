#!/usr/bin/env python3
"""Small-sample test suite for lecture-to-exam.

Everything runs offline, and nothing is written inside the skill directory: all
generated html/pdf go to a temp dir, so an installed (possibly read-only) skill
can be tested as-is.

Tests:
  1. env check runs and reports status
  2. md -> html -> pdf, blockquote hard breaks (SKIP when deps are absent)
  3. original slide image end to end (image really embedded) + verify_output gate,
     positive and negative
  4. review-mode guard: 2 lectures accepted, 1 rejected (exit 2)
  5. zoom_transcript helpers (offline): timestamps, JSON/VTT parsing,
     transcript-spec output, NO_TRANSCRIPT exit code, language detection
  6. knowledge-spec structure (offline, regex-based)
  7. review-spec structure (offline): text-only, 11 parts, five-line points,
     80-200 char Chinese paragraphs, exam hints
  8. run.py portability: works from a foreign cwd (no `cd` into the skill)

Run:  python3 tests/run_tests.py
Env:  PYTHON_BIN to test a specific interpreter.
"""
import os
import re
import sys
import shutil
import tempfile
import subprocess

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(SK, "scripts")
FIX = os.path.join(SK, "tests", "fixtures")
RUN = os.path.join(SCRIPTS, "run.py")
PY = os.environ.get("PYTHON_BIN") or sys.executable
NODE = os.environ.get("NODE_BIN") or shutil.which("node") or "node"

passed, failed, skipped = [], [], []
TMP = tempfile.mkdtemp(prefix="lte_tests_")


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def report(name, ok, detail=""):
    (passed if ok else failed).append(name)
    print(("PASS " if ok else "FAIL ") + name + ((" :: " + detail) if detail else ""))


def report_skip(name, detail=""):
    skipped.append(name)
    print("SKIP " + name + ((" :: " + detail) if detail else ""))


def has_md():
    return run([PY, "-c", "import markdown"]).returncode == 0


def copy_fixture_with_figures(dest):
    """Copy a fixture and its figures/ so relative image paths still resolve."""
    os.makedirs(dest, exist_ok=True)
    shutil.copy(os.path.join(FIX, "sample_knowledge_with_figures.md"), dest)
    src_fig = os.path.join(FIX, "figures")
    if os.path.isdir(src_fig):
        shutil.copytree(src_fig, os.path.join(dest, "figures"), dirs_exist_ok=True)
    return os.path.join(dest, "sample_knowledge_with_figures.md")


# --------------------------------------------------------------------------- #
def test_env():
    r = run([PY, RUN, "check_env"])
    report("1. check_env.py runs", r.returncode in (0, 1),
           r.stdout.strip().splitlines()[-1] if r.stdout else "")


def test_pipeline():
    md = os.path.join(FIX, "sample_lecture_L03.md")
    html = os.path.join(TMP, "l03.html")
    pdf = os.path.join(TMP, "l03.pdf")

    if not has_md():
        report_skip("2a. md_to_html.py", "python module 'markdown' not installed")
    else:
        r1 = run([PY, RUN, "md_to_html", md, html])
        report("2a. md_to_html.py", r1.returncode == 0 and os.path.exists(html),
               r1.stderr.strip().splitlines()[-1] if r1.stderr else "")

    test_blockquote_breaks()

    if not has_md():
        report_skip("2b. html_to_pdf.js", "no HTML produced (markdown missing)")
    else:
        r2 = run([NODE, os.path.join(SCRIPTS, "html_to_pdf.js"), html, pdf])
        err = r2.stderr.strip()
        env_missing = r2.returncode == 1 and ("playwright" in err.lower() or "chromium" in err.lower())
        if env_missing:
            report_skip("2b. html_to_pdf.js", "playwright/chromium not installed")
        else:
            report("2b. html_to_pdf.js",
                   r2.returncode == 0 and os.path.exists(pdf) and os.path.getsize(pdf) > 1000,
                   err.splitlines()[-1] if err else "")


def test_blockquote_breaks():
    """Regression: consecutive `>` lines must stay on separate lines in HTML,
    otherwise the four-/five-line blocks merge into one paragraph."""
    sys.path.insert(0, SCRIPTS)
    import importlib
    mht = importlib.import_module("md_to_html")

    sample = "> line1\n> line2\n> line3\n\npara1\npara2\n\n```\n> code line\n> code line\n```\n"
    out = mht.add_blockquote_breaks(sample)
    lines = out.split("\n")
    ok_helper = (
        lines[0].endswith("  ") and lines[1].endswith("  ")
        and not lines[2].endswith("  ")
        and not lines[4].endswith("  ")
        and not lines[8].endswith("  ")
    )
    report("2c. blockquote hard-break helper", ok_helper)

    # Render through PY (the interpreter under test), not this process: the
    # launcher may be a bare system python without `markdown`.
    probe = (
        "import sys\n"
        f"sys.path.insert(0, {SCRIPTS!r})\n"
        "import markdown, md_to_html as m\n"
        "h = markdown.markdown(m.add_blockquote_breaks('> a\\n> b\\n'), extensions=['tables'])\n"
        "print('YES' if '<br' in h else 'NO')\n"
    )
    r = run([PY, "-c", probe])
    if r.returncode != 0:
        report_skip("2d. four-line block renders as separate lines",
                    "module 'markdown' missing in the interpreter under test")
        return
    report("2d. four-line block renders as separate lines", "YES" in r.stdout)


def test_images_and_gate():
    work = os.path.join(TMP, "figures_case")
    md = copy_fixture_with_figures(work)
    html = os.path.join(work, "notes.html")
    pdf = os.path.join(work, "notes.pdf")

    if not has_md():
        report_skip("3a. original slide image embedded in PDF", "module 'markdown' missing")
    else:
        r1 = run([PY, RUN, "md_to_html", md, html])
        if r1.returncode != 0:
            report("3a. original slide image embedded in PDF", False, r1.stderr.strip()[-200:])
        else:
            r2 = run([NODE, os.path.join(SCRIPTS, "html_to_pdf.js"), html, pdf])
            err = r2.stderr.strip()
            if r2.returncode == 1 and ("playwright" in err.lower() or "chromium" in err.lower()):
                report_skip("3a. original slide image embedded in PDF",
                            "playwright/chromium not installed")
            else:
                ok = (r2.returncode == 0 and "image requests failed: none" in err
                      and os.path.getsize(pdf) > 1000)
                report("3a. original slide image embedded in PDF", ok,
                       err.splitlines()[-1] if err else "")

    r = run([PY, RUN, "verify_output", md, "--slides", "2"])
    report("3b. verify_output passes the Mode A fixture", r.returncode == 0,
           r.stdout.strip().splitlines()[-1] if r.stdout else "")

    broken = os.path.join(work, "no_caption.md")
    with open(md, encoding="utf-8") as f:
        body = f.read()
    with open(broken, "w", encoding="utf-8") as f:
        f.write(re.sub(r"^\*图：.*\*$", "", body, flags=re.M))
    r = run([PY, RUN, "verify_output", broken])
    report("3c. verify_output rejects a missing image caption",
           r.returncode == 1 and "FAIL A5" in r.stdout)

    r = run([PY, RUN, "verify_output", os.path.join(FIX, "sample_lecture_L03.md"),
             "--allow-text-only"])
    report("3d. --allow-text-only accepts a text-only handout", r.returncode == 0,
           r.stdout.strip().splitlines()[-1] if r.stdout else "")

    review = os.path.join(FIX, "sample_review_text_only.md")
    r = run([PY, RUN, "verify_output", review])
    report("3e. verify_output passes the Mode B fixture", r.returncode == 0,
           r.stdout.strip().splitlines()[-1] if r.stdout else "")

    polluted = os.path.join(TMP, "review_with_image.md")
    with open(review, encoding="utf-8") as f:
        body = f.read()
    with open(polluted, "w", encoding="utf-8") as f:
        f.write(body + "\n![x](figures/F_p12.png)\n")
    r = run([PY, RUN, "verify_output", polluted])
    report("3f. verify_output rejects an image inside a Mode B handbook",
           r.returncode == 1 and "FAIL B1" in r.stdout)


def test_guard():
    f1 = os.path.join(FIX, "sample_lecture_L03.md")
    f2 = os.path.join(FIX, "sample_lecture_L04.md")
    r_ok = run([PY, RUN, "validate_review_input", f1, f2])
    report("4a. review mode accepts 2 lectures", r_ok.returncode == 0,
           r_ok.stdout.strip().splitlines()[0] if r_ok.stdout else "")
    r_bad = run([PY, RUN, "validate_review_input", f1])
    report("4b. review mode rejects 1 lecture (exit 2)", r_bad.returncode == 2,
           r_bad.stderr.strip().splitlines()[0] if r_bad.stderr else "")


def test_zoom_transcript_helpers():
    sys.path.insert(0, SCRIPTS)
    try:
        import zoom_transcript as zt
    except Exception as e:  # noqa: BLE001
        report("5a. zoom_transcript helpers import", False, str(e))
        return
    ok_ts = zt.mmss("01:02:03.456") == "62:03" and zt.mmss("00:00:07.100") == "00:07"
    report("5a. timestamp parsing", ok_ts)

    data = [
        {"startTime": "00:16:30.350", "text": " Hello ", "userName": "prof@uni.edu"},
        {"startTime": "00:16:34.740", "text": "", "userName": "prof@uni.edu"},
    ]
    segs = zt.segments_from_json(data, with_speaker=True)
    ok_json = len(segs) == 1 and segs[0] == ("00:16:30.350", "prof@uni.edu: Hello")
    report("5b. JSON transcript parsing", ok_json)

    vtt = "WEBVTT\n\n1\n00:16:30.350 --> 00:16:32.230\nprof@uni.edu: Alright, let's stop.\n\n"
    vsegs = zt.segments_from_vtt(vtt, with_speaker=False)
    ok_vtt = len(vsegs) == 1 and vsegs[0][1] == "Alright, let's stop."
    report("5c. WebVTT parsing", ok_vtt)

    out = os.path.join(TMP, "_zt_test.md")
    n = zt.write_transcript(out, "sample", "Zoom official cloud transcript",
                            [("00:16:30.350", "Hello")])
    body = open(out, encoding="utf-8").read() if os.path.exists(out) else ""
    ok_write = (n == 1 and body.startswith("# 转录稿") and "---" in body
                and "- Transcript source: Zoom official cloud transcript" in body
                and "[16:30] Hello" in body)
    report("5d. transcript-spec output", ok_write)

    try:
        zt.no_transcript("official transcript status=absent")
        ok_exit = False
    except SystemExit as e:
        ok_exit = (e.code == 3)
    report("5e. NO_TRANSCRIPT exits with code 3", ok_exit)

    ok_lang = (zt.detect_language([("", "hello world")]) == "en"
               and zt.detect_language([("", "防火墙规则")]) == "zh")
    report("5f. transcript language detection", ok_lang)


def test_knowledge_spec_structure():
    md = os.path.join(FIX, "sample_knowledge_with_figures.md")
    if not os.path.exists(md):
        report("6. knowledge-spec fixture", False, "fixture missing")
        return
    s = open(md, encoding="utf-8").read()

    items = re.split(r"^#### ", s, flags=re.M)[1:]
    ok_four = all(
        all(f"**{k}**" in item for k in ("EN · 资料", "EN · 录音", "中", "📍 Source"))
        for item in items
    ) and len(items) >= 2
    report("6a. four-line knowledge blocks", ok_four, f"{len(items)} items")

    imgs = re.findall(r"!\[([^\]]+)\]\((figures/[^)]+)\)", s)
    captions = re.findall(r"^\*图：([^\n]+)\*$", s, flags=re.M)
    has_figure_block = "**资料图示**" in s
    ok_img = has_figure_block and len(imgs) >= 1 and len(captions) >= 1
    report("6b. original image + caption", ok_img, f"{len(imgs)} images, {len(captions)} captions")

    ok_col = "| Image |" in s and "— (blank)" in s
    map_paths = set(re.findall(r"\|\s*(figures/[^|\s]+)\s*\|", s))
    embed_paths = set(p for _, p in imgs)
    ok_agree = ok_col and bool(embed_paths) and embed_paths.issubset(map_paths)
    report("6c. page-map Image column agreement", ok_agree,
           f"embedded={sorted(embed_paths)} mapped={sorted(map_paths)}")

    ok_fixture_files = all(
        os.path.isfile(os.path.join(FIX, p)) for p in embed_paths | map_paths
    )
    report("6d. fixture images really exist on disk", ok_fixture_files)


def test_review_spec_structure():
    md = os.path.join(FIX, "sample_review_text_only.md")
    if not os.path.exists(md):
        report("7. review-spec fixture", False, "fixture missing")
        return
    s = open(md, encoding="utf-8").read()

    ok_noimg = ("![" not in s) and ("figures/" not in s)
    report("7a. review handbook is text-only (no images)", ok_noimg)

    chapters = set(re.findall(r"^## (\d+)\.", s, flags=re.M))
    ok_chap = chapters == {str(i) for i in range(1, 12)}
    report("7b. 11-part chapter order", ok_chap, f"chapters={sorted(chapters)}")

    items = re.split(r"^#### ", s, flags=re.M)[1:]
    keys = ("EN · 资料", "EN · 录音", "关键词", "中（一段话）", "📍 Source")
    ok_five = len(items) >= 2 and all(all(f"**{k}**" in it for k in keys) for it in items)
    report("7c. five-line knowledge blocks", ok_five, f"{len(items)} items")

    lengths = []
    for it in items:
        m = re.search(r"\*\*中（一段话）\*\*\s*·\s*(.+)", it)
        if m:
            lengths.append(len(re.findall(r"[\u4e00-\u9fff]", m.group(1))))
    ok_para = len(lengths) == len(items) and all(80 <= n <= 200 for n in lengths)
    report("7d. Chinese paragraph 80-200 chars", ok_para, f"lengths={lengths}")

    hints = ("考法", "作答", "考试", "应写", "写入答案", "应试")
    hot = [it for it in items if it.startswith("🔴") or it.startswith("🟠")]
    ok_hint = bool(hot) and all(any(h in it for h in hints) for it in hot)
    report("7e. 🔴/🟠 points carry exam hints", ok_hint, f"{len(hot)} hot points")


def test_run_py_portability():
    """The whole point of run.py: usable from any cwd, no `cd` into the skill."""
    r = run([PY, RUN, "--list"], cwd=TMP)
    report("8a. run.py --list works from a foreign cwd",
           r.returncode == 0 and "verify_output" in r.stdout)

    r = run([PY, RUN, "check_env"], cwd=TMP)
    report("8b. run.py check_env works from a foreign cwd",
           r.returncode in (0, 1) and "environment check" in r.stdout)

    html = os.path.join(TMP, "portability.html")
    r = run([PY, RUN, "md_to_html", os.path.join(FIX, "sample_lecture_L03.md"), html], cwd=TMP)
    if not has_md():
        report_skip("8c. run.py picks an interpreter with the deps", "module 'markdown' missing")
    else:
        report("8c. run.py picks an interpreter with the deps",
               r.returncode == 0 and os.path.exists(html),
               r.stderr.strip().splitlines()[-1] if r.stderr else "")

    r = run([PY, RUN, "no_such_tool"], cwd=TMP)
    report("8d. unknown tool fails cleanly (exit 1)", r.returncode == 1 and "unknown tool" in r.stderr)


def main():
    print("lecture-to-exam small-sample tests")
    print("=" * 52)
    try:
        test_env()
        test_pipeline()
        test_images_and_gate()
        test_guard()
        test_zoom_transcript_helpers()
        test_knowledge_spec_structure()
        test_review_spec_structure()
        test_run_py_portability()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print("=" * 52)
    print(f"passed: {len(passed)}  failed: {len(failed)}  skipped: {len(skipped)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
