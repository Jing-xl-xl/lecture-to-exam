#!/usr/bin/env node
/*
 * Dump the visible text of a JS-rendered page (share links, meeting summaries,
 * exam briefings). Static fetchers only see the app shell on such pages.
 *
 * Usage: node _dump_page.js <url> <out.txt> [scrollSteps]
 * Exit: 0 ok | 1 setup problem
 */
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execSync } = require("child_process");

const [url, outPath, scrollArg] = process.argv.slice(2);
const STEPS = Number(scrollArg || 8);

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
  try { for (const d of fs.readdirSync(npxRoot)) dirs.push(path.join(npxRoot, d, "node_modules")); } catch (e) {}
  return dirs;
}
function loadPlaywright() {
  try { return require("playwright"); } catch (e) {}
  for (const d of moduleDirs()) { try { return require(path.join(d, "playwright")); } catch (e) {} }
  return null;
}
function cachedChromium() {
  const home = os.homedir();
  const roots = [process.env.PLAYWRIGHT_BROWSERS_PATH];
  if (process.platform === "darwin") roots.push(path.join(home, "Library", "Caches", "ms-playwright"));
  roots.push(path.join(home, ".cache", "ms-playwright"));
  const names = new Set(["chrome", "chrome.exe", "chrome-headless-shell", "chrome-headless-shell.exe", "Google Chrome for Testing"]);
  const found = [];
  const walk = (dir, depth) => {
    if (depth > 5) return;
    let entries; try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (e) { return; }
    for (const e of entries) {
      const full = path.join(dir, e.name);
      if (e.isDirectory()) walk(full, depth + 1); else if (names.has(e.name)) found.push(full);
    }
  };
  for (const r of roots) if (r && fs.existsSync(r)) walk(r, 0);
  return found;
}
(async () => {
  const pw = loadPlaywright();
  if (!pw) { console.error("ERROR: playwright not found"); process.exit(1); }
  let browser;
  try { browser = await pw.chromium.launch(); } catch (e) {
    const exes = cachedChromium();
    for (const exe of exes) { try { browser = await pw.chromium.launch({ executablePath: exe }); break; } catch (e2) {} }
  }
  if (!browser) { console.error("ERROR: cannot launch chromium"); process.exit(1); }
  const page = await browser.newPage({ viewport: { width: 1280, height: 2000 } });
  await page.goto(url, { waitUntil: "networkidle", timeout: 60000 }).catch((e) => console.error("note: " + String(e.message).split("\n")[0]));
  await page.waitForTimeout(4000);
  for (let i = 0; i < STEPS; i++) { await page.mouse.wheel(0, 2000); await page.waitForTimeout(600); }
  const text = await page.evaluate(() => document.body.innerText);
  fs.writeFileSync(outPath, text);
  console.error("wrote " + outPath + " (" + text.length + " chars)");
  await browser.close();
})();
