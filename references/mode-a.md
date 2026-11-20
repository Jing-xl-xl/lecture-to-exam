# Mode A — single lecture (知识点讲义)

Load this when the user wants one lecture turned into notes. Read `SKILL.md`
first for the invocation contract and the hard rules.

Output: `<Course>_L<N>_知识点与考点.md` + `figures/` + a self-contained `.pdf`.

---

## A1 — Transcript (official Zoom transcript only)

### 1. Try the official transcript first

```bash
python3 "$SKILL_ROOT/scripts/run.py" zoom_transcript "<share-url>" \
  -o "work/L<N>/01_transcript.md" [--with-speaker]
```

The script walks `window.__zm_unified_player__` → feature-config API →
transcript getApi, with a WebVTT fallback. Domain and Referer are derived from
the URL; override with `--domain` / `--referer` only if detection fails. Any
share token of the same recording keeps working, because the UUID is stable.

Branch on the exit code — do not guess:

| Exit | Meaning | Action |
|---|---|---|
| `0` | transcript written | go to **A1 gate** |
| `3` + `NO_TRANSCRIPT` | host did not enable the official transcript | audio-only path below, then stop |
| `1` + `ERROR:` | access/network problem — password, expired link, SSO, curl failure | fix access; **not** the no-transcript case |

Never treat `1` as "no transcript". Never invent a transcript from the audio.

> Risk note: this reads Zoom's own player API, which is not a documented public
> contract. If it starts returning `ERROR:` where it used to work, suspect an API
> change before suspecting the recording.

### 2. No official transcript → download audio only, then stop

- Old `/rec/play/` links (yt-dlp):

  ```bash
  python3 "$SKILL_ROOT/scripts/run.py" zoom_fetch "<url>" -o "<course>_L<N>.m4a"
  # SSO: --cookies-from-browser chrome; probe first with --simulate
  ```

- New `/rec/share/` links (yt-dlp fails with "Unable to extract data"):

  ```bash
  python3 "$SKILL_ROOT/scripts/run.py" zoom_fetch_share "<url>" -o "<course>_L<N>.m4a"
  ```

Then tell the user, in their language:

> 该录制没有 Zoom 官方转录；音频已下载到 `<path>`。本 skill 不做转录，请自行转录，
> 并按 `references/transcript-spec.md` 的 `[mm:ss] 文本` 格式返回转录稿。

**Stop.** Do not continue to A2 until a transcript exists. This skill bundles no
transcription engine by design.

### 3. User supplies a transcript directly

Skip steps 1–2, check it against `references/transcript-spec.md`, then go to the
gate.

### A1 gate

Show: the transcript head plus segment/timestamp statistics, the source
(`Zoom official cloud transcript` or `User-supplied`), the detected language, and
the timestamp format. Wait for approval before using it downstream or writing the
final transcript file.

---

## A2 — Knowledge points + original slide images

### 1. Extract the materials

```bash
# PDF: text + page PNGs (120 dpi)
python3 "$SKILL_ROOT/scripts/run.py" extract_pdf course.pdf --prefix I --figures ./figures

# PPTX: page accounting only — never a substitute for images
python3 "$SKILL_ROOT/scripts/run.py" extract_pptx deck.pptx

# PPTX: original slide PNGs (130 dpi) — the required image source
python3 "$SKILL_ROOT/scripts/run.py" render_pptx_pages deck.pptx --prefix C --figures ./figures
```

Assign each supplied source a one-letter prefix from its filename (`F`, `C`,
`P`, `I`, `A`, `T` …) and document the mapping at the top of the `.md`.

### 2. No working LibreOffice — three outs, in this order

Do not silently downgrade to a text-only handout. Offer the user:

1. **Point at an existing install:** `render_pptx_pages deck.pptx --lo-app "/path/to/LibreOffice.app"`.
2. **Mount a DMG (macOS only):** `--dmg "/path/to/LibreOffice.dmg"`.
3. **Convert first:** the user exports the deck to PDF in PowerPoint / Keynote /
   LibreOffice, then you run `extract_pdf` on that PDF.

If the user still cannot produce images, stop and ask explicitly. Only if they
accept a text-only handout in so many words, continue and run the gate with
`--allow-text-only`. A silent text-only notes file is a failure.

### 3. Write the notes

Read the transcript and **every page of every source**. Follow
`references/knowledge-spec.md` exactly. The essentials:

- Eight chapters in the prescribed order, `####` per knowledge point, priority
  markers 🔴 / 🟠 / 🟢.
- Four lines per point, all four always present:
  `**EN · 资料**` (verbatim from slides) / `**EN · 录音**` (verbatim from the
  recording, quoted) / `**中**` (one short Chinese gloss) / `**📍 Source**`.
  A missing side is written `无对应引文`.
- Each non-blank page image is embedded **once**, beside the first point that
  quotes that page, in exactly this shape:

  ```markdown
  **资料图示**
  ![📄F p.12](figures/F_p12.png)
  *图：📄F p.12 — 该页原始幻灯片。*
  ```

  Later reuse of a page writes `（图见 §N）` instead of repeating the image.
  Never crop, redraw, or retype a slide.
- §8 Source Page-Map: one row per supplied page, with `Image` =
  `figures/{prefix}_p{NN}.png` or `— (blank)` for a skipped blank slide.
- Official Zoom timestamps may be cited directly; for user-supplied transcripts
  cite `mm:ss` only when the user confirmed the timestamps.

### 4. Run the gate

```bash
python3 "$SKILL_ROOT/scripts/run.py" verify_output work/L<N>/02_outline.md \
  --mode a --slides <number of supplied slides>
```

Exit `1` lists exactly what is missing. Fix it, then re-run. A handout that
fails the gate is not ready to show.

### A2 gate

Show the full Markdown content — including image placement and the page-map.
Wait for approval before writing the `.md`, copying `figures/`, and generating
the PDF.

---

## A3 — PDF companion

Run from the directory containing the `.md` and `figures/` (relative image paths
resolve there):

```bash
python3 "$SKILL_ROOT/scripts/run.py" md_to_html  <name>.md   <name>.html
python3 "$SKILL_ROOT/scripts/run.py" html_to_pdf <name>.html <name>.pdf
```

- `md_to_html` needs Python `markdown`; `html_to_pdf` needs Node + Playwright +
  Chromium. `run.py` picks the interpreter, so no manual `cd` or `PYTHONPATH`.
- `html_to_pdf` prints `image requests failed: none` on success. If any image
  request fails it deletes the partial PDF and exits `2` — fix the image, do not
  retry blindly.
- The PDF must open in WPS / Preview / a browser with all images embedded. Show
  the resulting paths to the user.

---

## Resume

If `work/L<N>/03_notes.md` already exists and passes `verify_output`, skip A1/A2
and go straight to the A2 gate with that draft. Never redo work silently just
because the session restarted.
