#!/usr/bin/env node
/* box-check: measured shell boxes on $BASE/ (fresh load, tiered) at 375, 768,
 * 1024 and 1440 wide, after document.fonts.ready.
 *
 * Usage:  BASE=http://localhost:<p> node scripts/box-check.mjs --boxes <json>
 *
 * Each box entry: { selector, _fields?: "x,y,width,height", "<width>": [..] | null }.
 * `null` means the element is absent or has zero size. Values must be within
 * `tolerance_px`. The home game grid (columns, children, 1440 filler count) is
 * read from the json's `grid` entry, or from the guide's measured table when the
 * json has none. Prints the selector used per box and `BOXES OK`. */

import { readFileSync, existsSync } from "node:fs";
import { chromium } from "playwright";

const WIDTHS = [375, 768, 1024, 1440];

/* Guide 02-01 "Measured boxes" (game grid rows) and 02-03 filler math. */
const GRID_DEFAULT = {
  selector: 'section[aria-label="Trò chơi"]',
  games: 16,
  375: { columns: 3, columnWidth: 103.66, children: 17 },
  768: { columns: 4, columnWidth: 172, children: 17 },
  1024: { columns: 6, columnWidth: 142, children: 21 },
  1440: { columns: 8, columnWidth: 112.5, children: 21, fillers: 5 },
};

function parseArgs(argv) {
  let boxes = null;
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--boxes") {
      boxes = argv[++i];
      if (!boxes || boxes.startsWith("--")) throw new Error("--boxes needs a value");
    } else throw new Error(`unknown argument ${argv[i]}`);
  }
  if (!boxes) throw new Error("--boxes <json> is required");
  return { boxes };
}

function measure(entries) {
  const out = {};
  for (const [name, selector] of entries) {
    const el = document.querySelector(selector);
    if (!el) {
      out[name] = null;
      continue;
    }
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    out[name] = r.width === 0 || r.height === 0 || cs.display === "none" ? null : { x: r.x, y: r.y, width: r.width, height: r.height };
  }
  return out;
}

function measureGrid(selector) {
  const root = document.querySelector(selector);
  if (!root) return null;
  const grid = [root, ...root.querySelectorAll("*")].find((n) => getComputedStyle(n).display === "grid" && n.children.length > 0);
  if (!grid) return null;
  const cols = getComputedStyle(grid).gridTemplateColumns.split(/\s+/).filter(Boolean).map(parseFloat);
  return { columns: cols.length, columnWidth: cols[0] ?? 0, children: grid.children.length };
}

async function main() {
  let opts;
  try {
    opts = parseArgs(process.argv.slice(2));
  } catch (e) {
    console.error(`box-check: ${e.message}`);
    return 1;
  }
  const base = (process.env.BASE ?? "").replace(/\/+$/, "");
  if (!base) {
    console.error("box-check: BASE is not set (run under scripts/with-dev-server.mjs)");
    return 1;
  }
  if (!existsSync(opts.boxes)) {
    console.error(`box-check: ${opts.boxes} not found`);
    return 1;
  }
  const spec = JSON.parse(readFileSync(opts.boxes, "utf8"));
  const tol = Number(spec.tolerance_px ?? 1);
  const height = Number(spec.viewport_height ?? 900);
  const route = spec.route ?? "/";
  const grid = spec.grid ?? GRID_DEFAULT;
  if (!spec.grid) console.log("box-check: grid expectations from the guide's measured table (no `grid` entry in the json)");
  const entries = Object.entries(spec.boxes ?? {}).map(([name, b]) => [name, b.selector]);
  for (const [name, selector] of entries) console.log(`box ${name}: ${selector}`);
  console.log(`box grid: ${grid.selector}`);

  const fails = [];
  const browser = await chromium.launch();
  try {
    for (const w of WIDTHS) {
      const ctx = await browser.newContext({ viewport: { width: w, height }, deviceScaleFactor: 1 });
      const page = await ctx.newPage();
      await page.goto(base + route, { waitUntil: "networkidle", timeout: 120000 });
      await page.evaluate(() => document.fonts.ready.then(() => true));
      await page.waitForTimeout(300);
      const got = await page.evaluate(measure, entries);
      for (const [name, b] of Object.entries(spec.boxes ?? {})) {
        const want = b[String(w)];
        if (want === undefined) continue;
        const fields = (b._fields ?? "x,y,width,height").split(",");
        const g = got[name];
        if (want === null) {
          if (g !== null) fails.push(`Fail: ${name}@${w} | Expected: absent or zero-size | Got: ${fmt(fields.map((f) => g[f]))}`);
          continue;
        }
        if (g === null) {
          fails.push(`Fail: ${name}@${w} | Expected: ${fmt(want)} | Got: absent`);
          continue;
        }
        const vals = fields.map((f) => g[f]);
        if (vals.some((v, k) => Math.abs(v - want[k]) > tol)) fails.push(`Fail: ${name}@${w} | Expected: ${fmt(want)} ±${tol} | Got: ${fmt(vals)}`);
        else console.log(`ok ${name}@${w} ${fmt(vals)}`);
      }
      const gw = grid[String(w)];
      if (gw) {
        const g = await page.evaluate(measureGrid, grid.selector);
        if (!g) fails.push(`Fail: grid@${w} | Expected: a grid inside ${grid.selector} | Got: none`);
        else {
          const errs = [];
          if (g.columns !== gw.columns) errs.push(`columns ${g.columns} (want ${gw.columns})`);
          if (gw.columnWidth !== undefined && Math.abs(g.columnWidth - gw.columnWidth) > tol) errs.push(`column width ${g.columnWidth} (want ${gw.columnWidth})`);
          if (g.children !== gw.children) errs.push(`children ${g.children} (want ${gw.children})`);
          if (gw.fillers !== undefined && g.children - grid.games !== gw.fillers) errs.push(`fillers ${g.children - grid.games} (want ${gw.fillers})`);
          if (errs.length) fails.push(`Fail: grid@${w} | Expected: ${JSON.stringify(gw)} | Got: ${errs.join(", ")}`);
          else console.log(`ok grid@${w} ${g.columns} x ${g.columnWidth}, ${g.children} children`);
        }
      }
      await ctx.close();
    }
  } finally {
    await browser.close();
  }
  for (const f of fails) console.error(f);
  if (fails.length) {
    console.error(`BOXES FAILED ${fails.length}`);
    return 1;
  }
  console.log("BOXES OK");
  return 0;
}

const fmt = (a) => a.map((v) => (typeof v === "number" ? Math.round(v * 10) / 10 : v)).join(",");

process.exit(await main());
