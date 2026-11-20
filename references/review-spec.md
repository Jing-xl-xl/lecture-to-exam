# Review handbook format spec

This reference defines the output of **Mode B (review handbook)**. It is derived
from repeated real runs on ICOM7128 (Knowledge Graphs) and ECOM6013
(E-commerce Technology) final-exam open-book preparation, refined against the
ICOM6045 L5/L6 + 2024 past-paper run. Follow it closely.

## Standing requirements

1. **B-system review handbook** — the default product form: a navigable exam
   guide + modular notes + terminology glossary + past-paper answers + a
   question-type playbook. If the user asks for "简答要点卡" (flash-answer cards)
   instead, switch form after confirming.
2. **Bilingual, parallel** — English and Chinese side by side, but with a clear
  division of labour: English = **verbatim** material + lecturer's own words (for copying into
   an open-book answer); Chinese = a keyword line for fast scanning + **one full
  explanatory paragraph** (what it is / why it matters / how it is examined).
  Keep the two languages visibly separated; never merge them into one line.
3. **Chinese summary = one paragraph, never a one-line gloss.** Each `中（一段话）`
   line must be **80–200 Chinese characters**, 3–6 sentences, written as one
   coherent paragraph. It must cover, in order: (a) what the point is / how it
   works, (b) why it matters and how it connects to other course material,
   (c) how it may be asked and what to write — only when the supplied material
   supports a weighting or exam hint; otherwise write `考法：资料未明示`.
   See `Per-knowledge-point pattern` below.
4. **NO IMAGES — zero tolerance.** The review handbook is a **text-only**
   document. Do **not** embed, copy, link, or reference any slide image, figure,
   screenshot, or past-paper figure anywhere in the handbook. Original slide
   PNGs belong **only** in Mode A single-lecture notes. Where the source lecture
   used a figure, describe its content in words inside the Chinese paragraph
   or the table cell; if a past-paper question contains a figure, transcribe
   the relevant information as plain text/Markdown table, never as an image.
   Section/page references are written as text (e.g. `📄F p.12`), not linked
   image paths. Do not create a `figures/` directory for the handbook.
5. **Verbatim source text** — where the original wording matters, quote the
   lecture notes' `EN · 资料` / `EN · 录音` lines word-for-word, with no
   paraphrase and no ellipsis ("...") that omits content.
6. **Only supplied material. No outside knowledge.** The handbook is an
   aggregation, not a new textbook. Never invent an answer, a definition, a
   marking scheme, or a "will definitely be examined" claim that the supplied
   notes/past papers do not support.
7. **Uncovered = explicit placeholder.** When a past-paper question falls
   outside the supplied lectures, write the analysis from the question text but
   set the answer to exactly:
   `本次输入未覆盖；需补充对应讲义或官方答案；未自行补写。`
   Do not fill the gap from general knowledge. List the gap again in §10.
8. **详实** — cover every exam-relevant point from all supplied lectures; do
   not omit content because it seems minor.
9. **Navigable** — the reader must locate a point fast during an open-book exam.
   Three navigation tables (§4) + a pure-text quick-reference (§10) are mandatory,
   not optional.
10. **Delivery** — a Markdown file plus a self-contained PDF. No images exist
    in either. PDF content must be verbatim-identical to the Markdown.

## Inputs

- **≥2 finished lecture knowledge `.md` files** (Mode A output). Fewer than two
  is rejected by `validate_review_input.py`.
  Their `figures/` folders are **not** inputs to Mode B: read the lecture text
  only, and never carry images over.
- Exam outline / exam-focus slides (often the final lecture's Course Review
  section — treat it as the authoritative skeleton of the whole course).
- Past-paper question papers and official answer sheets, if supplied. Any
  figure in them is read and converted to plain text, not reproduced.
- If only one year of past papers is supplied, say so explicitly in §3 and
  never infer that a topic recurs annually.

## Chapter order (11 parts — follow exactly)

1. **使用与考场指南 · How to use this handbook** — what the symbols mean
   (`🔴` core / `🟠` required / `🟢` context, `★` high-frequency), how to read it
   before the exam, how to locate a point in an open-book exam, and the rule
   "copy the English original into the answer when possible". State that the
   handbook is deliberately text-only for fast searching and printing.
2. **知识框架 · Knowledge map** — one-sentence course overview; what each
   supplied lecture contributes; the thread connecting the modules; one
   framework table grounded only in the supplied notes (text cells only).
3. **考试总纲 · Exam syllabus / exam facts** — exam format, weighting, question
   count, time budget and the verb-action taxonomy (`list` / `describe` /
   `explain` / `calculate` / `compare`) **only when the supplied material states
   them**. Add a one-line sample-size note, e.g. "仅 1 年真题样本，不推断年年必考".
   If no exam facts were supplied, write `本次输入未提供考试形式信息；未自行补写。`
4. **导览地图三表 · Three navigation tables**
   - 主题速查表: theme → section → source lecture → keyword.
   - `★` 高频考点清单: high-frequency points; `🔴` equals `★`; say why each is
     high-frequency (lecturer emphasis and/or past-paper appearance) — never
     assert recurrence without evidence.
   - 跨模块关联表: point A ↔ point B across lectures, with both section numbers.
5. **考点大纲总表 · Exam-point master table** — theme × priority × source
   lecture × keyword × appeared-in-past-paper (yes/no/未覆盖). Derive the
   skeleton from the lecturer's own Course Review where present.
6. **分模块考点 · Knowledge modules** — the body. One module per major topic;
   each point uses the five-line pattern below. **No images.** Where a slide
   carried a diagram, the Chinese paragraph describes it in words and the
   📍 Source line cites the page number as plain text.
7. **往年真题解析 · Past-paper analysis** — one entry per question using the
   expanded pattern below. Question figures are converted to text/tables.
8. **题型模板与答题套路 · Question-type templates** — templates derived ONLY
   from the supplied notes and past papers (e.g. a firewall rule table, an IDS
   base-rate / alarm-precision calculation, an SQL-injection analysis). Each
   template names its source entry; never write "每年必考" unless multiple years
   prove it.
9. **术语表 · Terminology glossary** — EN → CN → one-line note, as a table.
10. **纯文本速查表 + 需补讲义清单 · Quick reference & gaps** — a plain-text or
    minimal table of keyword → one-line answer for last-minute scanning,
    followed by every uncovered past-paper question from §7 (number + topic),
    each pointing to which lecture notes / official answer must be added. No filled-in answers.
11. **来源讲义索引 · Source lecture index** — which lecture file (and, where
    relevant, which section) each handbook module came from; makes aggregation
    auditable and confirms no supplied lecture was dropped. Cite page numbers
    only as text (`📄F p.12`), never as image links.

## Per-knowledge-point pattern

```markdown
#### 🔴 <Topic / point name>
> **EN · 资料** · <verbatim from the source lecture's "EN · 资料" line; 无对应引文 if none>
> **EN · 录音** · <verbatim from the source lecture's "EN · 录音" line; 无对应引文 if none>
> **关键词** · <中文关键词串，分号隔开，速查用>
> **中（一段话）** · <80–200 字的完整中文段落：是什么/怎么运作 → 为什么重要/与其他模块的关系 → 考试怎么考/作答要点（无依据写"考法：资料未明示"）>
> **📍 Source** · <L05 · 📄F p.12 · 📼 Recording (2026-11-17)>   ← 纯文字，无图片链接
```

- This is a **five-line** pattern: two English lines, one keyword line, one
  Chinese paragraph line, one source line. Never drop a line, never merge the
  two EN lines, and never shorten `中（一段话）` into a tag-style gloss.
- The Chinese paragraph is written as **one continuous block** (no bullet list
  inside it). A slide diagram, when relevant, is described inside this paragraph.
- Reuse the priority markers `🔴` Core (exam focus) · `🟠` Required · `🟢` Context.
  `🔴` is equivalent to `★` in the navigation tables — use one consistently.
- **Exam-hint rule:** `🔴` and `🟠` points MUST end their Chinese paragraph with a
  concrete exam hint (how it is asked / what to write / weighting if stated).
  `🟢` context points only explain; they may omit the exam hint.
- Source pointers must name the originating lecture (L05, L06, ...), so the
  aggregation stays traceable. Page references are plain text only.

## Past-paper entry pattern (expanded)

```markdown
### 2024 Q1 — <short title>

- **原题 (Question):** <verbatim question text; if the paper has a figure,
  transcribe its information as plain text / a Markdown table — NEVER an image>
- **题目解析 (Analysis):** <what the question is really testing>
- **考点分析 (Exam point):** <which syllabus topic(s) it maps to, with section link>
- **答案 (Answer):** <derived strictly from the supplied notes, OR exactly:
  本次输入未覆盖；需补充对应讲义或官方答案；未自行补写。>
- **给分点拆解 (Marking points):** <only when derivable from the supplied notes;
  otherwise: 本次输入未提供给分点；未自行补写。>
- **可抄英文原句 (Copyable English):** <verbatim English line from a supplied
  lecture that can be written into the answer; otherwise: 无对应英文原句。>
- **解题思路 (Approach):** <step-by-step reasoning, in bilingual form>
- **📍 Source:** <past-paper file / page + lecture file / section>   ← 纯文字
```

No image may appear in any field. When a question is covered, the derived
answer must cite the exact note entry it came from; when it is not covered, no
answer is fabricated.

## Priority and weighting

- When the lecturer stated grading weights or "this will be in the exam", mark
  those points 🔴/`★` and say so explicitly, citing the source.
- Where past papers across multiple years repeat a topic, escalate its priority
  and note the exact years. With a single year, do not claim recurrence.

## Delivery and PDF

- Write `<Course>_期末复习手册.md` (plus optional separate
  `<Course>_考点大纲.md` / `<Course>_真题解析.md` when large).
- Do NOT create or copy any `figures/` directory. Verify the final Markdown has
  zero `![...](...)` image syntax before conversion.
- Convert each to PDF with the shared Stage A3 commands:
  `md_to_html.py` then `html_to_pdf.js`.
- PDF must mirror the Markdown exactly; **no images**, A4, black/white/gray.

## Pitfalls

- Do NOT re-run transcription or re-read raw audio for Mode B — it consumes
  finished lecture notes, not recordings.
- Do NOT blend English originals and Chinese glosses into one line.
- Do NOT write a one-sentence `中` value. If it is shorter than a paragraph or
  reads like a label, rewrite it as a full 80–200 character paragraph.
- Do NOT carry any image from Mode A into Mode B, including past-paper figures.
  Text/tables only. A handbook with `![` is a failure.
- Do NOT silently drop a lecture: every supplied lecture file must contribute at
  least one cited section (verify against §11 Source lecture index).
- Do NOT invent answers, marking schemes, or "必考" claims for uncovered topics.
- Keep the handbook self-contained; a reader who only has the PDF must be able
  to use it in the exam without opening the source lectures.
