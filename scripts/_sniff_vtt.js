#!/usr/bin/env node
/*
 * Open a Zoom player page in a real browser and capture its transcript.
 *
 * The modern Zoom player renders client-side: the share page no longer embeds
 * a feature-config object, so zoom_transcript.py cannot read it with curl. The
 * player does fetch an official transcript though, as a WebVTT track:
 *     /rec/play/vtt?type=transcript&fid=...
 * This helper loads the page with the caller's cookies and writes that VTT out.
 *
 * Usage: node _sniff_vtt.js <url> <cookies.json> <out.json> [waitMs]
 * Output JSON: { title, vtt, playInfo, error }
 * Exit: 0 captured | 2 page opened but no VTT (no official transcript)
 *       1 setup problem (playwright/chromium/cookie file)
 */
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execSync } = require("child_process");

const [url, cookiesPath, outPath, waitArg] = process.argv.slice(2);
const WAIT_MS = Number(waitArg || 25000);

function moduleDirs() {
  const home = os.homedir();
  const dirs = [];
  for (const p of (process.env.NODE_PATH || "").split(path.delimiter)) if (p) dirs.push(p);
  dirs.push(path.join(__dirname, "..", "node_modules"));
  dirs.push(path.join(process.cwd(), "node_modules"));
  dirs.push(path.join(home, "node_modules"));
  try {
    const g = execSync("npm root -g", { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
    if (g) dirs.push(g);
  } catch (e) {}
  const npxRoot = path.join(home, ".npm", "_npx");
  try {
    for (const d of fs.readdirSync(npxRoot)) dirs.push(path.join(npxRoot, d, "node_modules"));
  } catch (e) {}
  return dirs;
}

function loadPlaywright() {
  try { return require("playwright"); } catch (e) {}
  for (const d of moduleDirs()) {
    try { return require(path.join(d, "playwright")); } catch (e) {}
  }
  return null;
}

// A pinned Chromium revision is often missing; any cached build can render a page.
function cachedChromium() {
  const home = os.homedir();
  const roots = [process.env.PLAYWRIGHT_BROWSERS_PATH];
  if (process.platform === "darwin") roots.push(path.join(home, "Library", "Caches", "ms-playwright"));
  if (process.platform === "win32") roots.push(path.join(process.env.LOCALAPPDATA || "", "ms-playwright"));
  roots.push(path.join(home, ".cache", "ms-playwright"));
  const names = new Set(["chrome", "chrome.exe", "chrome-headless-shell", "chrome-headless-shell.exe", "Google Chrome for Testing"]);
  const found = [];
  const walk = (dir, depth) => {
    if (depth > 5) return;
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (e) { return; }
    for (const e of entries) {
      const full = path.join(dir, e.name);
      if (e.isDirectory()) walk(full, depth + 1);
      else if (names.has(e.name)) found.push(full);
    }
  };
  for (const r of roots) if (r && fs.existsSync(r)) walk(r, 0);
  return found;
}

async function launch(pw) {
  const errors = [];
  const exes = cachedChromium();
  try { return await pw.chromium.launch(); } catch (e) { errors.push(String(e.message).split("\n")[0]); }
  for (const exe of exes) {
    try { return await pw.chromium.launch({ executablePath: exe }); } catch (e) { errors.push(String(e.message).split("\n")[0]); }
  }
  throw new Error("cannot launch chromium: " + errors.join(" | "));
}

(async () => {
  const pw = loadPlaywright();
  if (!pw) {
    fs.writeFileSync(outPath, JSON.stringify({ error: "playwright not found" }));
    console.error("ERROR: playwright not found (npm i playwright && npx playwright install chromium)");
    process.exit(1);
  }
  let cookies = [];
  try { cookies = JSON.parse(fs.readFileSync(cookiesPath, "utf8")); } catch (e) {}

  let browser;
  try { browser = await launch(pw); } catch (e) {
    fs.writeFileSync(outPath, JSON.stringify({ error: String(e.message) }));
    console.error("ERROR: " + e.message);
    process.exit(1);
  }

  const ctx = await browser.newContext({
    userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
  });
  if (cookies.length) await ctx.addCookies(cookies);

  let vtt = "";
  let info = "";
  ctx.on("response", async (res) => {
    const u = res.url();
    if (!vtt && /vtt\?type=transcript|\.vtt(\?|$)/i.test(u)) {
      try {
        const ct = res.headers()["content-type"] || "";
        if (/vtt|text/i.test(ct)) vtt = await res.text();
      } catch (e) {}
    } else if (!info && /play\/info|feature-config/i.test(u)) {
      try { info = await res.text(); } catch (e) {}
    }
  });

  const page = await ctx.newPage();
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
  } catch (e) {
    console.error("note: goto " + String(e.message).split("\n")[0]);
  }
  const started = Date.now();
  while (Date.now() - started < WAIT_MS && !vtt) await page.waitForTimeout(500);

  const title = await page.title().catch(() => "");
  await browser.close();
  fs.writeFileSync(outPath, JSON.stringify({ title, vtt, playInfo: info.slice(0, 20000) }));
  if (!vtt) {
    console.error("NO_TRANSCRIPT: page opened (" + title.slice(0, 60) + ") but no transcript track was captured");
    process.exit(2);
  }
  console.error("captured VTT (" + vtt.length + " chars)");
})();
