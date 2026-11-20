#!/usr/bin/env node
/*
 * Print a Markdown-derived HTML file to a self-contained A4 PDF.
 *
 * Loads HTML via file:// so relative `figures/...` paths resolve against the
 * HTML's own directory, waits for images, then prints with printBackground so
 * blockquotes / table headers / image borders are preserved. Every image is
 * embedded at print time, so the PDF needs no relative paths to display.
 *
 * Usage:
 *   node html_to_pdf.js <input.html> [output.pdf]
 *
 * Playwright resolution (portable, no hardcoded machine paths):
 *   1. normal require("playwright")
 *   2. NODE_PATH env var
 *   3. common local install locations: cwd/node_modules, ~/node_modules,
 *      and npx scratch installs under ~/.npm/_npx/<hash>/node_modules
 * If none resolve, a clear install hint is printed. Browser is resolved by
 * Playwright itself; install once with `npx playwright install chromium`.
 *
 * Logs `image requests failed: none` on success. Any failed image request
 * causes exit 2 and the partial PDF is deleted, so a PDF with broken images
 * is never left behind to ship.
 */
const path = require("path");
const fs = require("fs");
const os = require("os");
const { execSync } = require("child_process");

function playwrightCandidates() {
  const list = [];
  if (process.env.NODE_PATH) {
    process.env.NODE_PATH.split(path.delimiter).forEach((p) => p && list.push(p));
  }
  const home = os.homedir();
  // Skill-local first, then the user's project, then global installs. No host
  // specific path: this must work under any agent that ships this skill.
  list.push(path.join(__dirname, "..", "node_modules"));
  list.push(path.join(process.cwd(), "node_modules"));
  list.push(path.join(home, "node_modules"));
  try {
    const g = execSync("npm root -g", { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
    if (g) list.push(g);
  } catch (e) {}
  try {
    const npxRoot = path.join(home, ".npm", "_npx");
    if (fs.existsSync(npxRoot)) {
      fs.readdirSync(npxRoot).forEach((d) => list.push(path.join(npxRoot, d, "node_modules")));
    }
  } catch (e) {}
  return list;
}

function loadPlaywrightModule() {
  try { return require("playwright"); } catch (e) {}
  for (const c of playwrightCandidates()) {
    try { return require(path.join(c, "playwright")); } catch (e) {}
  }
  return null;
}

const CACHE_BIN_NAMES = new Set([
  "chrome", "chrome.exe",
  "chrome-headless-shell", "chrome-headless-shell.exe",
  "Google Chrome for Testing",
]);

function chromiumCacheRoots() {
  const home = os.homedir();
  const roots = [process.env.PLAYWRIGHT_BROWSERS_PATH];
  if (process.platform === "darwin") roots.push(path.join(home, "Library", "Caches", "ms-playwright"));
  if (process.platform === "win32") roots.push(path.join(process.env.LOCALAPPDATA || "", "ms-playwright"));
  roots.push(path.join(home, ".cache", "ms-playwright"));
  return roots.filter((r) => r && fs.existsSync(r));
}

// Any Chromium already downloaded can print a PDF. This keeps export working
// after a partial `playwright install`, where the module pins a revision that
// is not in the cache (a common failure that used to look like "PDF is broken").
function findCachedChromium() {
  const found = [];
  const walk = (dir, depth) => {
    if (depth > 5) return;
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (e) { return; }
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full, depth + 1);
      else if (CACHE_BIN_NAMES.has(entry.name)) found.push(full);
    }
  };
  chromiumCacheRoots().forEach((root) => walk(root, 0));
  return found;
}

async function launchBrowser() {
  const pw = loadPlaywrightModule();
  if (!pw) {
    console.error("ERROR: playwright not found. Install with: npm i playwright && npx playwright install chromium");
    process.exit(1);
  }
  // A playwright module can exist yet fail to launch if its expected chromium
  // revision is not installed. Try the module from every candidate location
  // and keep the first one that actually launches a browser.
  const attempts = [pw];
  for (const c of playwrightCandidates()) {
    try { attempts.push(require(path.join(c, "playwright"))); } catch (e) {}
  }
  const errors = [];
  const cached = findCachedChromium();
  for (const candidate of attempts) {
    try {
      return await candidate.chromium.launch();
    } catch (e) {
      errors.push(String(e.message || e).split("\n")[0]);
    }
    for (const exe of cached) {
      try {
        const browser = await candidate.chromium.launch({ executablePath: exe });
        console.error("note: pinned Chromium missing, using cached build: " + exe);
        return browser;
      } catch (e) {
        errors.push(String(e.message || e).split("\n")[0]);
      }
    }
  }
  console.error("ERROR: no playwright install could launch chromium. Tried:");
  errors.forEach((e) => console.error("  - " + e));
  console.error("Fix: npx playwright install chromium  (for the playwright version in use)");
  process.exit(1);
}

async function main() {
  const htmlPath = process.argv[2];
  if (!htmlPath) {
    console.error("Usage: html_to_pdf.js <input.html> [output.pdf]");
    process.exit(1);
  }
  const absHtml = path.resolve(htmlPath);
  const pdfPath = process.argv[3] || path.join(process.cwd(), path.basename(absHtml, ".html") + ".pdf");

  const browser = await launchBrowser();
  // Printing never needs scripts, and a Markdown file can carry raw HTML.
  // Run with JS off and only allow local resources, so converting someone
  // else's .md cannot execute code or phone home from this machine.
  const page = await browser.newPage({ javaScriptEnabled: false });
  await page.route("**/*", (route) => {
    const url = route.request().url();
    if (url.startsWith("file:") || url.startsWith("data:")) return route.continue();
    return route.abort();
  });

  const failed = [];
  page.on("requestfailed", (req) => {
    if (req.resourceType() === "image") failed.push(req.url());
  });

  await page.goto("file://" + absHtml, { waitUntil: "networkidle" });
  await page.pdf({
    path: pdfPath,
    format: "A4",
    printBackground: true,
    margin: { top: "15mm", bottom: "15mm", left: "15mm", right: "15mm" },
  });
  await browser.close();

  if (failed.length) {
    console.error("image requests failed: " + failed.join(", "));
    // Never leave a broken PDF behind that a caller could ship by mistake.
    try { fs.unlinkSync(pdfPath); } catch (e) {}
    process.exit(2);
  }
  console.error("image requests failed: none");
  console.log(pdfPath);
}

main().catch((e) => { console.error(e); process.exit(1); });
