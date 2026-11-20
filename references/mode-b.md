# Mode B — review handbook (复习资料)

Load this when the user wants a course-wide review handbook. Read `SKILL.md`
first for the invocation contract and the hard rules.

Output: `<Course>_期末复习手册.md` + `.pdf`, **text only**.

---

## B0 — Guard: two lectures minimum

```bash
python3 "$SKILL_ROOT/scripts/run.py" validate_review_input \
  lecture_notes/*.md --exam exam/2024.pdf
```

| Exit | Meaning | Action |
|---|---|---|
| `0` | valid | continue |
| `2` | fewer than two lectures | stop; ask for the remaining lecture notes |
| `3` | a lecture file is missing or unreadable | stop; ask for the correct path |

A directory of lecture `.md` files is accepted. Their `figures/` folders are
**not** inputs — read text only.

---

## B1 — Build the 11 parts, in this exact order

1. **使用与考场指南** — symbol legend (🔴 core / 🟠 required / 🟢 context, ★
   high-frequency), how to read before the exam, how to locate a point under
   time pressure, and the rule "copy the English original into the answer when
   possible". State that the handbook is deliberately text-only for searching and
   printing.
2. **知识框架** — one-sentence course overview, what each lecture contributes, the
   thread connecting modules, one framework table grounded only in the supplied
   notes.
3. **考试总纲** — format, weighting, question count, time budget, verb taxonomy
   (`list` / `describe` / `explain` / `calculate` / `compare`) **only if the
   supplied material states them**. Add a sample-size note ("仅 1 年真题样本，不推断年年必考"),
   or `本次输入未提供考试形式信息；未自行补写。`
4. **导览地图三表** — 主题速查 / ★高频清单 / 跨模块关联. Say *why* a point is
   high-frequency (lecturer emphasis and/or past-paper appearance); never assert
   recurrence from a single year.
5. **考点大纲总表** — theme × priority × lecture × keyword × appeared-in-past-paper
   (yes / no / 未覆盖). Build the skeleton from the lecturer's own Course Review
   where one was supplied.
6. **分模块考点** — the body, five lines per point (below). Describe any slide
   diagram in words inside the Chinese paragraph; cite pages as plain text.
7. **往年真题解析** — one entry per question, eight fields (below). Convert any
   question figure to text or a Markdown table.
8. **题型模板与答题套路** — templates derived only from the supplied notes and
   papers; name the source entry for each. Never write "每年必考" without
   multiple years of evidence.
9. **术语表** — EN → CN → one-line note, as a table.
10. **纯文本速查表 + 需补讲义清单** — keyword → one-line answer for last-minute
    scanning, then every uncovered question (number + topic) and which lecture or
    official answer must be added. No filled-in answers.
11. **来源讲义索引** — which lecture file (and section) each module came from.
    Confirms no supplied lecture was dropped.

Follow `references/review-spec.md` verbatim.

### Per-point pattern (five lines, never merged)

```markdown
#### 🔴 <Topic / point name>
> **EN · 资料** · <verbatim from the source lecture's EN · 资料 line; 无对应引文 if none>
> **EN · 录音** · <verbatim from the source lecture's EN · 录音 line; 无对应引文 if none>
> **关键词** · <中文关键词串，分号隔开>
> **中（一段话）** · <80–200 字一段话：是什么/怎么运作 → 为什么重要 → 怎么考/作答要点>
> **📍 Source** · <L05 · 📄F p.12 · 📼 Recording (2026-11-17)>
```

- `中（一段话）` is **one continuous paragraph** of 80–200 Chinese characters,
  no bullets inside it. A one-line gloss is a failure.
- 🔴 and 🟠 points must end with a concrete exam hint. 🟢 may omit it.
- Source lines name the originating lecture, so aggregation stays auditable.
- No `figures/` path may appear anywhere, even as plain text pointing at an
  image file.

### Past-paper entry pattern

```markdown
### 2024 Q1 — <short title>

- **原题 (Question):** <verbatim; figures transcribed as text/table>
- **题目解析 (Analysis):**
- **考点分析 (Exam point):** <syllabus topic + section link>
- **答案 (Answer):** <derived strictly from supplied notes, or exactly:
  本次输入未覆盖；需补充对应讲义或官方答案；未自行补写。>
- **给分点拆解 (Marking points):** <only if derivable; else:
  本次输入未提供给分点；未自行补写。>
- **可抄英文原句 (Copyable English):** <verbatim lecture line, or 无对应英文原句。>
- **解题思路 (Approach):** <step-by-step, bilingual>
- **📍 Source:** <past paper + page + lecture file/section>
```

A covered answer must cite the exact note entry it came from. An uncovered
question gets the placeholder and a line in §10 — never a general-knowledge
answer, never an invented marking scheme.

---

## B2 — Gate before delivery

```bash
python3 "$SKILL_ROOT/scripts/run.py" verify_output work/review_draft.md --mode b
```

It checks: zero image syntax, chapters 1–11 present and ordered, five-line blocks
complete, every `中（一段话）` between 80 and 200 Chinese characters and bullet-free,
every 🔴/🟠 carrying an exam hint. Exit `1` prints the offending item numbers.

Then show the whole handbook to the user and wait for approval before writing
`review/<Course>_期末复习手册.md`.

---

## B3 — Delivery

- Write `<Course>_期末复习手册.md` (plus optional `<Course>_考点大纲.md` /
  `<Course>_真题解析.md` when the material is large).
- **Do not create or copy a `figures/` directory.**
- Convert to PDF with the shared path:

  ```bash
  python3 "$SKILL_ROOT/scripts/run.py" md_to_html  <name>.md <name>.html
  python3 "$SKILL_ROOT/scripts/run.py" html_to_pdf <name>.html <name>.pdf
  ```

- PDF must mirror the Markdown exactly: A4, black/white/gray, no images.
- Show the resulting file paths to the user.

---

## Resume

If `review/<Course>_期末复习手册.md` already exists and passes
`verify_output --mode b`, do not rebuild it from scratch — confirm with the user
whether to extend or overwrite.
