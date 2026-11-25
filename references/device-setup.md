# Device setup — the author's tested machine

This file exists because "works on my machine" is not reproducible. Everything
below was verified end to end on the machine that produced the reference run
(two lectures, 91 slides, one exam paper).

## 1. Exact environment

| Item | Verified value | Why it matters |
|---|---|---|
| Machine | Apple Silicon (arm64) | Chromium paths carry `mac-arm64`; Intel needs `mac-x64` |
| OS | macOS 26.6.2 (build 25G83) | |
| Python | 3.15.2 (Homebrew, `/opt/homebrew/opt/python@3.15/bin/python3.15`) | the system interpreter has **no** `markdown` / `pymupdf` |
| Node | v22.23.4 (nvm) | |
| Playwright | 1.65.0-alpha-2026-10-30, from the npx cache | it pins a Chromium revision that is often not cached |
| Chromium (cache) | `chromium-1234`, `chromium-1254`, matching headless shells | the pinned `1252` was missing; the renderer falls back |
| LibreOffice | 25.8.7.3, **mounted from DMG** at `/Volumes/LibreOffice` | `/Applications` copy crashed with `DeploymentException` |
| Browser | Google Chrome 158.0.8127.37, signed in to the course Zoom tenant | `/rec/play/` transcripts need this session |
| Workspace | iCloud Drive (`~/Library/Mobile Documents/...`) | large course material syncs to the cloud |

## 2. Four traps on this machine

1. **`brew install` fails** — `/opt/homebrew` is owned by root.
   Fix once: `sudo chown -R $(whoami) /opt/homebrew /Users/$(whoami)/Library/Caches/Homebrew`.
2. **`npm install` fails** — `~/.npm` is owned by root.
   Workaround: `npm install --cache /tmp/npm-cache` (or fix ownership the same way).
3. **`timeout` does not exist** — macOS ships no GNU timeout.
   Use a background job, or the built-in timeouts in Playwright / curl.
4. **Writing outside the agent workspace** — sandboxed hosts deny it.
   Stage the output inside the workspace, then copy once with explicit permission.

## 3. Reproduce the reference run

```bash
# 1. isolated deps (do not touch the system Python)
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt browser_cookie3
npm install --cache /tmp/npm-cache && npx playwright install chromium

# 2. health check (per stage, not all-or-nothing)
python3 scripts/run.py check_env

# 3. transcript (share link first, then /rec/play/)
python3 scripts/run.py zoom_transcript "<share-url>" -o work/t.md
python3 scripts/run.py zoom_transcript_play "<play-url>" -o work/t.md --from-browser chrome

# 4. which decks did this recording actually teach?
python3 scripts/run.py match_decks --recording work/t.md --decks ../6045lecture10

# 5. slides -> images, notes, PDF
python3 scripts/run.py render_pptx_pages deck.pptx --prefix F --figures figures \
    --lo-app /Volumes/LibreOffice/LibreOffice.app
python3 scripts/run.py md_to_html notes.md notes.html
python3 scripts/run.py html_to_pdf notes.html notes.pdf

# 6. one-page A4 revision sheet
python3 scripts/run.py make_cheatsheet outline.md cheat.pdf
```

## 4. What was verified, and how

| Check | Result |
|---|---|
| Transcript, `/rec/share/` | 1151 and 1206 segments, official cloud transcript |
| Transcript, `/rec/play/` | 1032 and 1206 segments, captured from the player's VTT |
| Slide rendering | 44 + 47 + 34 + 40 pages at 130 dpi |
| PDF embedding | every PDF reported `image requests failed: none` |
| Format gate | 11/11 (Mode A) and 8/8 (Mode B) on real deliverables |
| Offline tests | 32 passed, 0 failed, 0 skipped |

## 5. When a value differs

Change one thing at a time and re-run `check_env`. The script prints the exact
path it selected, so a mismatch is visible immediately. If you override a tool,
prefer the environment variables (`PYTHON_BIN`, `NODE_BIN`, `SOFFICE_BIN`,
`PLAYWRIGHT_BROWSERS_PATH`) over editing the scripts.
