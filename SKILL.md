---
name: lecture-to-exam
description: |-
  Turns lecture recordings plus course slides into exam-ready study material, in
  two modes. Mode A: one Zoom share link with Zoom's official cloud transcript +
  that lecture's PDF/PPTX -> a bilingual knowledge-point Markdown (English
  verbatim + Chinese gloss) with every original slide rendered and embedded at
  full size, plus a self-contained PDF. If the recording has no official
  transcript, the skill downloads the audio only and stops; it never transcribes
  itself. Mode B: two or more finished lecture .md files + exam outline / past
  papers -> an 11-part TEXT-ONLY exam review handbook in Markdown and PDF.
  Triggers: 把录音整理成知识点, 总结这节课的知识点, 生成 lecture 讲义, 生成复习大纲,
  期末复习手册, 根据所有 lecture 整理考点, 转成 pdf, or a Zoom recording link for a
  course. Review mode needs at least two lectures.
license: MIT
---

# Lecture to Exam

One skill, two independent modes sharing the same scripts and format rules.
This file is the entry point and the rulebook. Stage-by-stage detail lives in
`references/` and should be loaded only when that mode actually runs.

- **Mode A — single lecture.** Recording + that lecture's slides →
  `figures/` original slide images + `<Course>_L<N>_知识点与考点.md` + PDF.
- **Mode B — review handbook.** Two or more finished lecture `.md` files +
  exam outline / past papers → an 11-part, text-only handbook + PDF.

Mode B consumes Mode A's output but never invokes it, and need not run in the
same session.

## 0. Invocation contract (read this first)

1. **`SKILL_ROOT`** is the directory containing this file. All tooling is
   addressed from there.
2. **Run tools only through `scripts/run.py`**, never by assuming the cwd is the
   skill directory:

   ```bash
   python3 "$SKILL_ROOT/scripts/run.py" <tool> [args...]
   python3 "$SKILL_ROOT/scripts/run.py" --list
   ```

   `run.py` resolves the skill root from its own location, picks a Python
   interpreter that can actually import what the tool needs, and forwards the
   exit code. On Windows use `py -3` or `python` in place of `python3`.
3. **Check the environment for the stage you are about to run**, not for
   everything: `run.py check_env --json` reports which stage each dependency
   serves. Do not tell the user to install tools the stage does not use.
4. **Reply in the user's language.** The deliverables keep the format their spec
   defines (English verbatim lines + Chinese summaries).

## 1. Routing

| User intent | Mode |
|---|---|
| One Zoom link + slides → lecture notes / 知识点 / 讲义 (with slide images) | A |
| Official transcript + slides already supplied → knowledge summary | A (skip A1) |
| "根据所有 lecture 生成复习大纲 / 期末复习手册 / 考点总结" | B |
| Existing lecture `.md` → PDF only | A, stage A3 only |
| An existing outline / mind map must be **completed** | C (`references/mode-c.md`) |
| Fewer than 2 lectures for a "review" request | B guard → ask for more |
| Zoom link is old-style `/rec/play/` | A1 via `zoom_transcript_play` (browser session + VTT) |
| Zoom link has no official transcript | A1 stops after audio download; ask the user for a transcript |
| PPTX supplied but no working LibreOffice | A2 stops; offer the three outs in `references/mode-a.md` |

## 2. Hard rules (non-negotiable)

1. **Approval gate before any final file.** Show the full draft to the user —
   in the conversation, not a file — and wait for explicit approval. Mode A has
   two gates (transcript, then knowledge outline); Mode B has at least one
   (review outline) before writing anything final. A draft may live under
   `work/`; a deliverable may not be written before approval.
2. **Transcript: Zoom's official cloud transcript only.** Always try
   `zoom_transcript.py` first. Exit `0` = available → gate 1. Exit `3` with
   `NO_TRANSCRIPT` → download audio only, then stop and ask the user for a
   transcript shaped by `references/transcript-spec.md`. Exit `1` with `ERROR:`
   → access problem (password, expiry, SSO, network), **not** a missing
   transcript; fix access first. Never transcribe locally, never recommend a
   specific transcription tool.
   For an old-style `/rec/play/` link, or when the share page no longer embeds
   the player config, `zoom_transcript` hands over to `zoom_transcript_play`,
   which borrows a signed-in browser session and captures the player's VTT.
   Cookies stay in a per-run temp dir and are deleted on exit; never print them
   and never persist them.
3. **Original slide images are mandatory in Mode A.** Every non-blank page
   becomes `figures/{prefix}_p{NN}.png`, embedded once at full size beside the
   first point that uses it, with a caption and a matching page number. If no
   working LibreOffice, stop and offer the outs in `references/mode-a.md` — never
   ship a text-only handout or fabricate images. Blank pages are logged in the
   page-map, not embedded.
4. **The PDF mirrors the Markdown exactly.** Conversion only repackages layout.
   If `html_to_pdf` reports a failed image, fix the image; never ship the broken
   PDF (the tool deletes it and exits `2`).
5. **Mode B is text-only, with paragraph Chinese summaries.** No slide image,
   screenshot, or `![...](...)` anywhere. Each point is five lines —
   `EN · 资料` / `EN · 录音` / `关键词` / `中（一段话）` / `📍 Source` — where
   `中（一段话）` is a full 80–200 character paragraph (是什么 / 为什么重要 /
   怎么考). 🔴🟠 points must end with a concrete exam hint. Never a one-line gloss.
6. **No machine-specific paths.** Every path comes from an argument, an
   environment variable, or this file's own location.
7. **Review mode needs ≥ 2 lectures.** Run `validate_review_input.py` before any
   synthesis; on exit `2`, stop and ask for more lectures.

## 3. Exit codes

| Code | Meaning | What to do |
|---|---|---|
| `0` | success | continue |
| `1` | operation failed: dependency, access/network, or a failed verification | read stderr; fix the cause; do not proceed |
| `2` | bad usage or insufficient input (e.g. < 2 lectures, broken PDF images) | fix the input or ask the user |
| `3` | `NO_TRANSCRIPT` (no official transcript) or a missing lecture file | take the audio-only / ask-for-path branch |

## 4. Artifacts and the work directory

```text
<course>/
├── work/                          # intermediate drafts; safe to delete
│   └── L5/
│       ├── 01_transcript.md       # gate-1 draft
│       ├── 02_outline.md          # knowledge outline draft
│       └── 03_notes.md            # exactly what gets approved
├── lecture_notes/
│   ├── figures/L5/F_p01.png ...   # original slide images
│   ├── ICOM6045_L5_知识点与考点.md
│   └── ICOM6045_L5_知识点与考点.pdf
└── review/
    ├── ICOM6045_期末复习手册.md
    └── ICOM6045_期末复习手册.pdf
```

**Resume:** if `work/<L>/03_notes.md` already exists and passes verification,
skip straight to the approval gate instead of redoing the work. The same applies
to `review/` when the handbook already verifies.

## 5. Verification gate

Before showing a draft as final — and before writing a deliverable — run:

```bash
python3 "$SKILL_ROOT/scripts/run.py" verify_output <file.md> --mode a [--slides N]
python3 "$SKILL_ROOT/scripts/run.py" verify_output <file.md> --mode b
```

It enforces, mechanically: four-/five-line blocks, image presence + on-disk
existence + caption + page-map agreement (Mode A), zero images and 11 parts and
80–200 character paragraphs and exam hints (Mode B). Exit `1` means the draft
violates its spec; fix it before the gate, not after. Use
`--allow-text-only` **only** when the user has explicitly accepted a text-only
handout.

## 6. References

| File | Load it when |
|---|---|
| `references/mode-a.md` | running Mode A (A1 transcript → A2 notes → A3 PDF) |
| `references/mode-b.md` | running Mode B (guard → 11 parts → PDF) |
| `references/transcript-spec.md` | validating or requesting a transcript |
| `references/knowledge-spec.md` | writing the Mode A `.md` |
| `references/review-spec.md` | writing the Mode B handbook |
| `references/mode-c.md` | completing an existing outline / mind map |
| `references/device-setup.md` | reproducing the author's environment |

| Tool | Purpose |
|---|---|
| `check_env` | read-only dependency check (`--json` for machines) |
| `verify_output` | the gate above |
| `zoom_transcript` | share links: official cloud transcript (curl only) |
| `zoom_transcript_play` | `/rec/play/` links: browser session + player VTT |
| `zoom_fetch` / `zoom_fetch_share` | audio-only fallback |
| `match_decks` | suggest which decks a recording actually taught |
| `make_cheatsheet` | markdown → one-page A4 revision sheet |
| `fetch_webpage_text` | render a JS page and dump its visible text |
| `extract_pdf` / `extract_pptx` / `render_pptx_pages` | source text and original page images |
| `validate_review_input` | enforces ≥ 2 lectures |
| `md_to_html` / `html_to_pdf` | Markdown → HTML → self-contained PDF |

## 7. Pitfalls

- Never substitute local transcription for a missing official transcript.
- User-supplied transcripts may get technical terms wrong — verify against the
  slides, and cite a precise `mm:ss` only when the user confirms timestamps.
- Verify the supplied deck matches the recording before writing. Decks are named
  by module, folders by session; if they diverge, stop and confirm.
- Supplied slides carry equal weight with the recording: every page is expanded
  into an item or logged in the page-map.
- "LibreOffice installed" is not the same as "LibreOffice works" — `check_env`
  starts it to prove it; a `DeploymentException` means broken.
- In Mode B, never answer an uncovered past-paper question from general
  knowledge; list it in the gap checklist instead.
- Keep `figures/...` paths relative in Mode A so the folder travels with the
  `.md`; the PDF is the self-contained artifact.
