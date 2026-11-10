#!/usr/bin/env node
/* shot-diff: compare a captured screenshot set against the reference set.
 *
 * Usage:  node scripts/shot-diff.mjs --ref <dir> --got <dir> --masks <json> --justify <json>
 *         node scripts/shot-diff.mjs --self-test
 *
 * JPEGs are decoded in headless Chromium. Per pair: size equality, the % of
 * pixels whose max channel delta exceeds `channel_threshold`, and that % outside
 * the mask boxes recorded in the manifests (`<dir>/manifest.json`, `masks`).
 * Prints `SHOTS OK 72/72` only when there are 72 reference files, none missing,
 * no unjustified size mismatch, and every pair is under `max_outside_mask_pct` or
 * justified. A size mismatch passes only when that pair has a justify row. */

import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { chromium } from "playwright";

const EXPECTED = 72;

function comparePair({ a, b, boxes, thr }) {
  const decode = async (b64) => {
    const res = await fetch("data:image/jpeg;base64," + b64);
    const bmp = await createImageBitmap(await res.blob());
    const c = new OffscreenCanvas(bmp.width, bmp.height);
    const g = c.getContext("2d");
    g.drawImage(bmp, 0, 0);
    return { w: bmp.width, h: bmp.height, d: g.getImageData(0, 0, bmp.width, bmp.height).data };
  };
  return Promise.all([decode(a), decode(b)]).then(([x, y]) => {
    if (x.w !== y.w || x.h !== y.h) return { sizeOk: false, ref: `${x.w}x${x.h}`, got: `${y.w}x${y.h}` };
    const n = x.w * x.h;
    const mask = new Uint8Array(n);
    for (const bx of boxes) {
      const x0 = Math.max(0, Math.floor(bx.x));
      const y0 = Math.max(0, Math.floor(bx.y));
      const x1 = Math.min(x.w, Math.ceil(bx.x + bx.width));
      const y1 = Math.min(x.h, Math.ceil(bx.y + bx.height));
      for (let yy = y0; yy < y1; yy++) mask.fill(1, yy * x.w + x0, yy * x.w + Math.max(x0, x1));
    }
    let diff = 0;
    let outside = 0;
    for (let i = 0, p = 0; i < n; i++, p += 4) {
      const m = Math.max(Math.abs(x.d[p] - y.d[p]), Math.abs(x.d[p + 1] - y.d[p + 1]), Math.abs(x.d[p + 2] - y.d[p + 2]));
      if (m > thr) {
        diff++;
        if (!mask[i]) outside++;
      }
    }
    return { sizeOk: true, ref: `${x.w}x${x.h}`, diffPct: (100 * diff) / n, outsidePct: (100 * outside) / n };
  });
}

function manifestMasks(dir) {
  const f = path.join(dir, "manifest.json");
  const map = new Map();
  if (!existsSync(f)) return map;
  for (const e of JSON.parse(readFileSync(f, "utf8"))) if (e && e.file) map.set(e.file, e.masks ?? []);
  return map;
}

function justifiedSet(file) {
  const data = JSON.parse(readFileSync(file, "utf8"));
  const set = new Set();
  if (Array.isArray(data)) for (const e of data) set.add(typeof e === "string" ? e : e.file);
  else for (const k of Object.keys(data)) if (!k.startsWith("_")) set.add(k);
  return set;
}

export async function run({ ref, got, masks, justify }, browser) {
  const lines = [];
  for (const [flag, p] of [["--ref", ref], ["--got", got], ["--masks", masks], ["--justify", justify]]) {
    if (!p || !existsSync(p)) return { code: 1, lines: [`shot-diff: ${flag} ${p ?? "(missing)"} not found`] };
  }
  const cfg = JSON.parse(readFileSync(masks, "utf8"));
  const thr = Number(cfg.channel_threshold ?? 16);
  const maxPct = Number(cfg.max_outside_mask_pct ?? 0.5);
  const okList = justifiedSet(justify);
  const refFiles = readdirSync(ref).filter((f) => f.endsWith(".jpg")).sort();
  const boxRef = manifestMasks(ref);
  const boxGot = manifestMasks(got);
  const page = await browser.newPage();
  let missing = 0;
  let sizeBad = 0;
  let over = 0;
  let pass = 0;
  try {
    for (const f of refFiles) {
      const g = path.join(got, f);
      if (!existsSync(g)) {
        missing++;
        lines.push(`Fail: ${f} | Expected: captured | Got: missing`);
        continue;
      }
      const boxes = [...(boxRef.get(f) ?? []), ...(boxGot.get(f) ?? [])];
      const r = await page.evaluate(comparePair, {
        a: readFileSync(path.join(ref, f)).toString("base64"),
        b: readFileSync(g).toString("base64"),
        boxes,
        thr,
      });
      if (!r.sizeOk) {
        if (okList.has(f)) {
          pass++;
          lines.push(`${f}: size ${r.ref} vs ${r.got} size mismatch (justified)`);
          continue;
        }
        sizeBad++;
        lines.push(`Fail: ${f} | Expected: size ${r.ref} | Got: ${r.got}`);
        continue;
      }
      const stat = `${f}: size ${r.ref} ok, diff ${r.diffPct.toFixed(3)}%, outside masks ${r.outsidePct.toFixed(3)}%`;
      if (r.outsidePct < maxPct) {
        pass++;
        lines.push(stat);
      } else if (okList.has(f)) {
        pass++;
        lines.push(`${stat} (justified)`);
      } else {
        over++;
        lines.push(`Fail: ${f} | Expected: outside masks < ${maxPct}% | Got: ${r.outsidePct.toFixed(3)}%`);
      }
    }
  } finally {
    await page.close();
  }
  if (refFiles.length === EXPECTED && missing === 0 && sizeBad === 0 && over === 0 && pass === EXPECTED) {
    lines.push(`SHOTS OK ${pass}/${EXPECTED}`);
    return { code: 0, lines };
  }
  lines.push(`SHOTS FAILED ${pass}/${EXPECTED} (reference files ${refFiles.length}, missing ${missing}, size mismatches ${sizeBad}, over threshold ${over})`);
  return { code: 1, lines };
}

async function selfTest(browser) {
  const tmp = mkdtempSync(path.join(tmpdir(), "shot-diff-"));
  const page = await browser.newPage();
  const jpeg = (opts) =>
    page.evaluate(({ w, h, hue, patch }) => {
      const c = document.createElement("canvas");
      c.width = w;
      c.height = h;
      const g = c.getContext("2d");
      g.fillStyle = `hsl(${hue} 40% 30%)`;
      g.fillRect(0, 0, w, h);
      g.fillStyle = "#e8e2c8";
      g.fillRect(4, 4, w - 8, 6);
      if (patch) {
        g.fillStyle = "#ff00ff";
        g.fillRect(patch.x, patch.y, patch.w, patch.h);
      }
      return c.toDataURL("image/jpeg", 0.72).split(",")[1];
    }, opts);
  const names = Array.from({ length: EXPECTED }, (_, i) => `m375-tiered-seed${String(i).padStart(2, "0")}.jpg`);
  const mk = (dir) => {
    const d = path.join(tmp, dir);
    mkdirSync(d, { recursive: true });
    return d;
  };
  const ref = mk("ref");
  for (const [i, n] of names.entries()) writeFileSync(path.join(ref, n), Buffer.from(await jpeg({ w: 40, h: 30, hue: i * 5 }), "base64"));
  const patch = { x: 20, y: 14, w: 12, h: 10 };
  const cloneWith = async (dir, change) => {
    const d = mk(dir);
    for (const n of names) writeFileSync(path.join(d, n), readFileSync(path.join(ref, n)));
    if (change) await change(d);
    return d;
  };
  const perturbed = async (d) =>
    writeFileSync(path.join(d, names[3]), Buffer.from(await jpeg({ w: 40, h: 30, hue: 15, patch }), "base64"));
  const masksFile = path.join(tmp, "masks.json");
  writeFileSync(masksFile, JSON.stringify({ channel_threshold: 16, max_outside_mask_pct: 0.5, selectors: ["time"] }));
  const noJustify = path.join(tmp, "justify-empty.json");
  writeFileSync(noJustify, "{}");
  const justify = path.join(tmp, "justify.json");
  writeFileSync(justify, JSON.stringify({ [names[3]]: "seeded random value" }));
  const justifySize = path.join(tmp, "justify-size.json");
  writeFileSync(justifySize, JSON.stringify({ [names[1]]: "seeded size cause" }));
  const resized = async (d) => writeFileSync(path.join(d, names[1]), Buffer.from(await jpeg({ w: 41, h: 30, hue: 5 }), "base64"));

  const cases = [
    ["identical set passes (0% self-diff)", await cloneWith("same"), noJustify, 0, ref],
    ["unmasked change fails", await cloneWith("changed", perturbed), noJustify, 1, ref],
    [
      "change inside a mask box passes",
      await cloneWith("masked", async (d) => {
        await perturbed(d);
        writeFileSync(path.join(d, "manifest.json"), JSON.stringify([{ file: names[3], masks: [{ selector: "time", x: patch.x - 8, y: patch.y - 8, width: patch.w + 16, height: patch.h + 16 }] }]));
      }),
      noJustify,
      0,
      ref,
    ],
    ["justified change passes", await cloneWith("justified", perturbed), justify, 0, ref],
    ["missing capture fails", await cloneWith("missing", async (d) => rmSync(path.join(d, names[0]))), noJustify, 1, ref],
    [
      "size mismatch fails",
      await cloneWith("size", async (d) => writeFileSync(path.join(d, names[1]), Buffer.from(await jpeg({ w: 41, h: 30, hue: 5 }), "base64"))),
      noJustify,
      1,
      ref,
    ],
    ["justified size mismatch passes", await cloneWith("size-justified", resized), justifySize, 0, ref],
    [
      "71 reference files fail",
      await cloneWith("same71"),
      noJustify,
      1,
      await (async () => {
        const d = await cloneWith("ref71");
        rmSync(path.join(d, names[71]));
        return d;
      })(),
    ],
  ];
  await page.close();
  let ok = 0;
  for (const [label, got, just, want, refDir] of cases) {
    const r = await run({ ref: refDir, got, masks: masksFile, justify: just }, browser);
    const pass = r.code === want && (want === 1 || r.lines.at(-1) === `SHOTS OK ${EXPECTED}/${EXPECTED}`);
    if (pass) ok++;
    console.log(`  seed ${label}: ${pass ? "ok" : "UNEXPECTED " + r.lines.at(-1)}`);
  }
  rmSync(tmp, { recursive: true, force: true });
  if (ok === cases.length) {
    console.log("SHOT-DIFF SELF-TEST OK");
    return 0;
  }
  console.log(`SHOT-DIFF SELF-TEST FAILED ${ok}/${cases.length}`);
  return 1;
}

function parseArgs(argv) {
  const o = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--self-test") o.selfTest = true;
    else if (["--ref", "--got", "--masks", "--justify"].includes(a)) {
      const v = argv[++i];
      if (v === undefined || v.startsWith("--")) throw new Error(`${a} needs a value`);
      o[a.slice(2)] = v;
    } else throw new Error(`unknown argument ${a}`);
  }
  return o;
}

async function main() {
  let o;
  try {
    o = parseArgs(process.argv.slice(2));
  } catch (e) {
    console.error(`shot-diff: ${e.message}`);
    return 1;
  }
  if (!o.selfTest && !(o.ref && o.got && o.masks && o.justify)) {
    console.error("shot-diff: --ref, --got, --masks and --justify are required");
    return 1;
  }
  const browser = await chromium.launch();
  try {
    if (o.selfTest) return await selfTest(browser);
    const r = await run(o, browser);
    for (const l of r.lines) console.log(l);
    return r.code;
  } finally {
    await browser.close();
  }
}

process.exit(await main());
