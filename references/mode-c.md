# Mode C — extending an existing synthesis document

Load this when the user already has a large framework document (a mind map, an
exam outline, a handbook) and wants it **completed**, not regenerated.

The rule: you are a surgeon, not a rewriter. Existing sections, numbering and
tone stay; you add at anchors, continue the numbering, and update the indexes
that would otherwise go stale.

## C1 — Read the frame before writing

1. Extract the heading skeleton (`^#{1,4} `) and read it end to end.
2. Identify the **numbering scheme** (M1…M7, T01…T62, E01…E30, W01…W20, X01…X17).
   New material must continue from the highest existing number, never restart.
3. Find the **declared gaps**: most frameworks carry a gap table or a
   "to be added" list. That list is your work order — do not invent new scope.
4. Note the per-section pattern (e.g. `一句话 / 类比 / 为什么考 / 关联`) and
   reproduce it exactly.

## C2 — Choose anchors, never reflow

- Insert **before** the next top-level chapter, not in the middle of a section.
- Keep the original separator/blank-line conventions.
- Never renumber existing sections. If the new material logically belongs in
  M7.3 but M7.2 is free, take M7.2 — order matters less than stability.
- If the document is bilingual, make the two files mirror each other
  section for section; do not let them drift.

## C3 — Write to the frame's density

- One knowledge point = one bullet with the same sub-labels the frame uses.
- Every claim keeps a source pointer (deck page / recording timestamp).
- Quotes are verbatim; paraphrases are marked as summaries.
- If the frame has examples, add examples with continued IDs; if it has term
  cards, add term cards. Do not introduce a new genre mid-document.

## C4 — Update the indexes

A completed document has four things that go stale silently:

| Index | Update |
|---|---|
| Table of contents / heading counts | new sections appear |
| Term cards / examples ranges in the title (`T01–T62` → `T01–T74`) | bump the range |
| Gap table | flip rows from "to add" to "done", keep genuinely missing rows |
| Document scope in the H1 (`L1–L6` → `L1–L7b`) | reflect the new coverage |

## C5 — Structural self-check (run it, do not eyeball it)

```bash
# headings, numbering continuity, code-fence balance, table rows
python3 - <<'PY'
import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
print("lines:", s.count("\n") + 1)
print("h2:", len(re.findall(r"^## ", s, re.M)))
print("fences balanced:", s.count("```") % 2 == 0)
nums = [int(n) for n in re.findall(r"^### T(\d+)", s, re.M)]
print("term cards:", len(nums), "contiguous:", nums == list(range(1, len(nums) + 1)))
PY
```

Then re-read the changed regions in context — a correct count does not prove the
prose joins up.

## Pitfalls

- Do not "improve" existing wording while adding a section; it hides your diff.
- Do not translate the whole document just to add one section.
- Do not leave the gap table claiming work is missing after you added it.
- Do not let the Chinese and English copies diverge in structure; a reader may
  use either one.
