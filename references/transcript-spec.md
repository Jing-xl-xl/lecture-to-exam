# Transcript Markdown format (source-agnostic contract)

This file defines the ONLY contract the rest of the skill depends on for the
transcript. Accepted sources:

  1. Zoom's official cloud transcript (`scripts/zoom_transcript.py`) — the only
     transcript source built into this skill. Preferred for Zoom share links:
     seconds-fast, accurate, precise timestamps.
  2. A transcript supplied by the user, produced outside this skill.

This skill does NOT transcribe audio and does NOT document any specific
transcription method. When a recording has no official transcript, the skill
downloads the audio only and stops; the user returns a transcript in the shape
below. Stages A2 / Mode B consume any transcript that follows this contract.

## Required shape

```markdown
# 转录稿 — <source-name>

- Transcript source: Zoom official cloud transcript | User-supplied
- Detected language: <code, e.g. en>
- Note: verify technical terms against the original slides before citing.

---

[00:00] <first segment text>
[00:07] <second segment text>
[01:23] <third segment text>
...
```

## Rules

1. A first-level heading naming the source.
2. A short metadata block: `Transcript source`, detected language, and the caveat
   about term accuracy.
3. A `---` separator.
4. One segment per line: `[mm:ss] text`. `mm:ss` is the segment start time.
5. Preserve the spoken wording; do NOT summarize. This file is the raw material
   for knowledge extraction, so completeness matters more than polish.
6. Encoding: UTF-8.

## User-supplied transcripts

- For Zoom links, first try `scripts/zoom_transcript.py` (official transcript).
- If it reports `NO_TRANSCRIPT`, the skill downloads audio only and stops; the
  user transcribes externally and returns a Markdown file in the format above.
- Put the actual source in `Transcript source:` (e.g. `User-supplied`).
- Everything downstream is source-agnostic.

## Note on timestamps

For **Zoom official transcripts**, timestamps are platform-generated and
reliable; a precise `mm:ss` may be cited directly. With `--with-speaker`, each
line is prefixed `speaker: text` so speaker turns can also be cited.

For **user-supplied transcripts**, cite a precise `mm:ss` only when the user
confirms that the timestamps are reliable. Otherwise use coarse source pointers
such as `📼 Recording`.
