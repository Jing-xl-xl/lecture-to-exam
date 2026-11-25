# Markdown Output Format Spec

This reference defines the exact Markdown structure produced by the
**lecture-to-exam** skill (Mode A, single lecture). Follow it verbatim so output is consistent
and machine/visually scannable.

## Standing requirements (non-negotiable)

1. **详实** — include every concept taught in the recording + PDFs. Never omit.
2. **English-first** — each item leads with the English original (verbatim from
   the recording or the PDF). The Chinese is a *short* gloss, not a full
   translation.
3. **Source pointer** on every item.
4. **A Markdown file plus a companion self-contained PDF.** The `.md` +
   `figures/` is the editable source; the PDF (images embedded, produced by
   Mode A Stage A3) is the primary shareable artifact and must be
   verbatim-identical in content.
5. **Source balance** — the supplied slide/PDF source(s) must be cited as
   heavily as the recording. No page/slide of any supplied source may be silently
   dropped; every page/slide is either expanded into an item or recorded in the
   Source Page-Map (§8 below).
6. **Split the English original by source.** Each item's English is written as
   two lines — `**EN · 资料**` (from the slide/PDF source(s)) and `**EN · 录音**`
   (from the recording). Single-source items mark the missing one as
   `无对应引文`. Do not merge both into one `EN` line.
7. **Original slide images are MANDATORY.** Every **non-blank** page/slide of a
   supplied PPTX (and of a supplied PDF when a renderer is available) must be
   rendered to `figures/{prefix}_p{NN}.png` and embedded **once**, at full size,
   in the chapter where that page first appears — with a caption and a matching
   `📍 Source` page number. No image may be cropped, redrawn, recoloured, or have
   its slide text retyped into the picture. A text-only handout is NOT an
   acceptable deliverable when the input is a slide deck.
8. **Image → knowledge-point binding.** The page image is placed immediately
   before or after the `####` item whose `EN · 资料` quote comes from that page.
   When a page supports several items, embed once at the first one and write
   `（图见 §N）` on later ones. Blank slides are logged in the page-map only.
9. **PPTX decks are first-class sources, handled identically to PDFs.** The word
   "PDF" in this skill means "the supplied slide/presentation source". Use
   `scripts/extract_pptx.py` (stdlib-only) for the page-by-page text account;
   use `scripts/render_pptx_pages.py` (LibreOffice) for the mandatory original
   images. Text extraction is an accounting aid, never a substitute for the
   images.

## Heading hierarchy

- `# Title` — course + session (e.g. `ICOM6045 L5 — Firewalls and Tunnels`)
- `###` — a one-line scope/format note under the title
- `>` blockquote — a "Format / Sources / Priority" legend at the top, including the
  source-letter mapping and a note that images are original rendered slides
- `##` — major chapters (order below)
- `####` — individual knowledge points (with priority marker)

## Priority markers (kept as emoji for scannability in plain Markdown)

- `🔴` Core — exam focus
- `🟠` Required — assignment / operational must-do
- `🟢` Context — platform / background / examples

## Per-item pattern

```markdown
#### 🔴 The six Initial Steps (Current State → Future State)
> **EN · 资料** · 1) Analyse the existing data system(s) · 2) Document the "current state" · 3) Identify the common key Entities and Relationships · 4) Develop a data instance example · 5) Develop the data graph model — the "future state" · 6) Focus on Interoperability.
> **EN · 录音** · 老师强调这六步不是一次性活动，而是贯穿整个 assignment 的迭代循环，尤其 interoperability 要在第一步就考虑。
> **中** · 作业方法论主线：分析现状 → 记录 current state → 抽取关键实体/关系 → 造数据实例 → 抽象出 future-state 图模型（本体）→ 强调互操作性。
> **📍 Source** · 📄A p.1 · 📼 Recording (S01-2)
```

(If an item is recording-only, the `EN · 资料` line reads `无对应引文`; if
slide-only, the `EN · 录音` line reads `无对应引文`. Both lines are always present.)

Rules:
- `**EN · 资料**` line: English verbatim from the slide/PDF source. Quote lists/code
  verbatim; keep the original wording. If the item is recording-only, write
  `无对应引文`.
- `**EN · 录音**` line: English verbatim from the recording. Quote spoken
  passages with `"..."`. If the item is slide-only, write `无对应引文`.
- `**中**` line: one concise Chinese explanation. Do **not** translate the whole
  English passage — summarize the key takeaway only.
- `**📍 Source**` line: cite with icons —
  - `📄A` = Assignment PDF, `📄T` = Tutorial PDF (append `p.N` page when known)
  - `📄F` … `📄S` = the supplied lecture decks/PDFs (letter from filename)
  - `📼` = lecture recording (append session id or date, or a confirmed
    `mm:ss` only when independently verified)
- Every `####` item MUST have all four lines.

## Source-pointer conventions

Assign each supplied source a **short letter from its filename** and document the
mapping once at the top of the file. The canonical letters below are the common
case; extend as needed.

| Icon | Meaning | Example |
|------|---------|---------|
| 📄O  | Course Overview PDF | `📄O p.3` |
| 📄I  | Introduction / lecture-slides PDF | `📄I p.12` |
| 📄A  | Assignment PDF | `📄A p.3` |
| 📄T  | Tutorial / software PDF | `📄T p.1` |
| 📄P  | Course-plan / outline deck (PPTX) | `📄P p.13` |
| 📄C  | Content / lecture-slides deck (PPTX) | `📄C p.42` |
| 📄D  | Second content deck (PPTX) | `📄D p.7` |
| 📄F  | Firewalls/Tunnels deck (PPTX) | `📄F p.12` |
| 📄S  | Generic slides deck (PPTX) | `📄S p.5` |
| 📼   | Lecture recording | `📼 Recording (2026-11-17)` |

**PPTX decks get a filename-derived letter too** — there is no separate rule for
`.pptx` vs `.pdf`; a deck is just another source. When two decks are supplied,
give each its own letter. If two files are md5-different but clearly the same
deck with trivial revisions, treat them as **one** logical source and do not
double-count pages.

When a fact appears in both the recording and a slide, list both. The source-icon
counts across the whole file should show the slide sources cited roughly as often
as `📼`.

## Embedding original slide images (MANDATORY)

- Save images as `figures/{prefix}_p{NN}.png` (prefix = source letter, NN =
  zero-padded page number). Render PPTX at ~130 dpi, PDF at ~120 dpi.
- **Skip blank slides.** A slide that is empty (title-only placeholder, section
  divider, "click to add notes" blank) is **not embedded**. The renderer may
  still emit a PNG for it; leave that file unreferenced. It is
  still listed in the Source Page-Map with `Treatment = Skip (blank)` and
  `Image = — (blank)` so the page count reconciles.
- Insert each non-blank page image **once**, at the chapter/item where it first
  appears, using exactly this three-line pattern:

  ```markdown
  **资料图示**

  ![📄D p.3](figures/D_p03.png)

  *图：📄D p.3 — DataDiscovery 第 3 页，展示 SPARQL 查询示例。*
  ```

  Keep a blank line between the label, the image, and the caption. Without
  them Markdown folds all three into one paragraph, and some renderers then
  paint the caption above the image.

  The caption must name the same source letter and page number as the image path
  and the linked `📍 Source` line. Do not paraphrase the slide: the image itself
  is the verbatim source.
- For a page reused later, do **not** repeat the image — add `（图见 §N）` at the
  later item.
- Recording-only items (no slide page) need no image.
- Keep image paths relative in the `.md` so it travels with its `figures/`
  folder. The self-contained deliverable is the PDF produced by Mode A Stage A3
  (images embedded at print time); no separate base64 step is needed.
- If a slide image is missing, broken, or was never rendered, **stop** — do not
  ship a text-only substitute and do not continue to PDF.

## PDF companion (produced by Mode A Stage A3)

The Markdown is converted to a self-contained A4 PDF so images display in any
reader (WPS, browsers, previewers) without relative-path failures. Conventions:

- **Page:** A4, `printBackground: true`, ~15 mm margins.
- **Style:** black/white/gray minimal — white background, light-gray blockquote,
  thin-bordered images, dark-slate table headers, 🔴🟠🟢 preserved.
- **Images:** embedded at native resolution (the `figures/*.png` are ≥120 dpi);
  never downscaled.
- **Content:** must be verbatim-identical to the Markdown — the conversion only
  changes layout, never facts.

## Recommended chapter order

1. **Course / Lecture Snapshot** — table: course, lecture, date, instructor, deck source(s), recording.
2. **Scope & Source Coverage** — what was supplied, source-letter mapping, image-render status, how missing sources are handled.
3. **Topic Map** — one-paragraph overview + a short table of module → section → priority.
4. **Knowledge Points by Module** — the body: `####` four-line blocks with the original slide images embedded beside the first item that uses each page (`🔴` / `🟠` / `🟢`).
5. **Worked Examples / Calculations** — only examples present in the supplied slides or recording; keep formulas and numbers verbatim.
6. **Exam-Point Summary** — priority × topic × keyword × source table.
7. **Glossary** — EN → CN → one-line note, as a table.
8. **Source Page-Map** — one row per supplied page/slide (below).

Do not copy chapters that do not fit the course (e.g. assignment grading or a software
stack for a course that has none). Keep the eight-chapter order when they do apply.

## Tables

Use GitHub-flavored Markdown tables for the snapshot, source coverage, topic map,
exam-point summary, glossary, and the source page-map. Keep them concise; long
explanations belong in the per-item blockquotes, not the table.

## Source Page-Map chapter (§8 — mandatory when slide/PDF sources are supplied)

This chapter proves coverage of the provided materials. One row per page/slide,
with an `Image` column that records where the original image went:

```markdown
## 8. Source Page-Map (课程资料逐页对照)

### 📄P — Course-plan deck (16 pages)
| Page | Content | Mapped to § | Necessity | Treatment | Image |
|------|---------|-------------|-----------|-----------|-------|
| 📄P p.1 | Course identity, semester, instructor | §1 | 🟢 | Brief | figures/P_p01.png |
| 📄P p.13 | Teaching plan (weekly schedule) | §3 | 🟠 | Expanded | figures/P_p13.png |

### 📄C — Content deck (90 pages)
| Page | Content | Mapped to § | Necessity | Treatment | Image |
|------|---------|-------------|-----------|-----------|-------|
| 📄C p.1 | Module title: Classical Encryption Techniques | §9 | 🔴 | Expanded | figures/C_p01.png |
| 📄C p.41 | (blank — section divider) | — | — | Skip (blank) | — (blank) |
| 📄C p.42 | Cryptanalysis of columnar transposition | §12 | 🔴 | Expanded | figures/C_p42.png |
```

Rules:
- **Every** page/slide of **every** supplied source appears exactly once. When
  multiple decks/PDFs are supplied, split into one sub-table per source so each
  sub-table's row count equals that source's page count. The grand total of rows
  equals the total pages/slides supplied.
- **Blank slides** are listed with `Treatment = Skip (blank)` and
  `Image = — (blank)`; they are not expanded or embedded, but the row keeps the
  page accounting complete.
- `Necessity` reuses the priority markers: 🔴 necessary detail (expanded into a
  full item), 🟠 required/operational (expanded), 🟢 supporting (condensed to a
  brief note but still cited).
- `Treatment` says `Expanded` (full per-item coverage exists), `Brief`
  (condensed to a short note), `Skip (blank)` (empty slide, listed only), or
  `Not taught` (deck supplied but this recording did not cover it).
- **Supplied but not covered.** When several decks are handed over and the
  recording only teaches some, list every unused deck in §2 with a one-line
  reason, and do not invent page rows for it. Run the gate with
  `--scope partial`, which requires that "not taught" note to exist.
- `Image` is the exact relative path `figures/{prefix}_p{NN}.png` when a non-blank
  page was rendered and embedded, or `— (blank)` for a skipped blank slide.
  A non-blank row with no image path is a coverage failure — stop and render it.
- A page reused in a later section still has exactly one `Image` cell here; the
  later section points back with `（图见 §N）`.

## Worked example (from real lectures)

The skill was first used on HKU **ICOM7128 Knowledge Graphs** (Prof. Renato
Iannella). The richer run covered **Lecture 1** from two recordings plus four
PDFs (29 pages) and produced a 55-item summary across 12 chapters, with all
pages rendered to `figures/*.png` and embedded once at first use — the concrete
quality bar for 详实 and for source balance.

The **Lecture 2** run introduced the `EN · 资料` / `EN · 录音` split on 82 items,
rendered **all 39** PDF pages to 120-dpi PNGs, embedded each once with a caption,
and listed every page in the page-map — the quality bar for the source-split +
image-embedding variant.

The **ICOM6045 Lecture 1** run is the reference case for **PPTX sources**: two
recordings plus a 16-page course-plan deck (`📄P`) and a 90-page cryptography
content deck (`📄C`), rendered through a mounted LibreOffice DMG to 130 dpi.
The §8 page-map was split into two sub-tables (16 + 90 = 106 rows), blank slides
(41/43/48) were logged as `Skip (blank)`, and a late-supplied deck upgraded
recording-only sections to dual-source while keeping every four-line block
complete. This is the quality bar for the PPTX variant: dual deck, split
page-map, blank-slide skipping, and original-image embedding.
