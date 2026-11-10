#!/usr/bin/env node
/* Contrast of the designer's overlay pairs (pairs.json, classes text 4.5, ui 3.0,
 * decorative 1.0) and the win/loss luminance rule, on the built .next/static CSS
 * of the tree in the cwd. Every pair token must resolve from the built CSS; there
 * is no JSON fallback. Win/loss: |La - Lb| / max(La, Lb) <= 5% (TOKENS.md:116).
 * Prints `CONTRAST OK n/n`, then `WINLOSS OK <pct>`. */

import { readFileSync } from "node:fs";
import path from "node:path";
import { DS_DIR, SCOPE, TARGET, colourOf, fail, loadBuilt, loaderMap, scopeMap, tryResolve } from "./css-lib.mjs";

const CLASSES = { text: 4.5, ui: 3.0, decorative: 1.0 };
const built = loadBuilt();
if (!built) {
  console.log(`Fail: contrast-build | Expected: ${path.join(TARGET, ".next/BUILD_ID")} (run npm run build) | Got: missing`);
  console.log("CONTRAST FAILED no build");
  process.exit(1);
}
const MAP = scopeMap(built.rules, SCOPE.base);
const LOADER = loaderMap(built.rules);
const pairs = JSON.parse(readFileSync(path.join(DS_DIR, "pairs.json"), "utf8"));

/* WCAG 2 relative luminance, same constants as the designer's check. */
const lin = (x) => (x / 255 <= 0.03928 ? x / 255 / 12.92 : ((x / 255 + 0.055) / 1.055) ** 2.4);
const lum = ([r, g, b]) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
const over = (top, under) => {
  const a = top[3];
  return [0, 1, 2].map((k) => top[k] * a + under[k] * (1 - a)).concat(1);
};
const hex = (c) => "#" + c.slice(0, 3).map((x) => Math.round(x).toString(16).padStart(2, "0")).join("") + (c[3] < 1 ? Math.round(c[3] * 255).toString(16).padStart(2, "0") : "");

let canvas = null;
{
  const r = tryResolve("--canvas", MAP, LOADER);
  canvas = r.error ? null : colourOf(r.value);
}
function colour(name, id) {
  const r = tryResolve(name, MAP, LOADER);
  if (r.error) { fail(id, `${name} resolves from .next/static`, r.error); return null; }
  const c = colourOf(r.value);
  if (!c) { fail(id, `${name} is one colour`, r.value); return null; }
  return c;
}

let n = 0, good = 0;
if (!Array.isArray(pairs) || pairs.length < 55) fail("contrast-pairs", "pairs.json: an array of >= 55 pairs", Array.isArray(pairs) ? pairs.length : typeof pairs);
for (const p of Array.isArray(pairs) ? pairs : []) {
  n++;
  const id = `contrast ${p.fg} on ${p.bg}`;
  if (CLASSES[p.class] !== p.min) { fail(id, "class text 4.5 | ui 3.0 | decorative 1.0", `${p.class} ${p.min}`); continue; }
  let fg = colour(p.fg_var, `${id} (${p.fg_var})`);
  let bg = colour(p.bg_var, `${id} (${p.bg_var})`);
  if (!fg || !bg) continue;
  if (bg[3] < 1) {
    if (!canvas) { fail(id, "an opaque --canvas under a translucent background", "unresolved"); continue; }
    bg = over(bg, canvas);
  }
  if (fg[3] < 1) fg = over(fg, bg);
  const [hi, lo] = [lum(fg), lum(bg)].sort((a, b) => b - a);
  const ratio = (hi + 0.05) / (lo + 0.05);
  if (ratio + 1e-9 >= p.min) good++;
  else fail(id, `${p.class} >= ${p.min.toFixed(1)}:1 (${p.fg_var} ${hex(fg)} on ${p.bg_var} ${hex(bg)})`, `${ratio.toFixed(2)}:1`);
}
const contrastOk = n >= 55 && good === n;
console.log(contrastOk ? `CONTRAST OK ${good}/${n}` : `CONTRAST FAILED ${good}/${n}`);

/* Win/loss: the pair names of feedback.win and feedback.loss in pairs.json. */
const nameOf = (ds) => { const p = pairs.find((x) => x.fg === ds) || pairs.find((x) => x.bg === ds); return p ? (p.fg === ds ? p.fg_var : p.bg_var) : null; };
const winName = nameOf("semantic.color.feedback.win");
const lossName = nameOf("semantic.color.feedback.loss");
let winlossOk = false;
if (!winName || !lossName) fail("WINLOSS", "feedback.win and feedback.loss pairs in pairs.json", `${winName} ${lossName}`);
else {
  const w = colour(winName, `WINLOSS ${winName}`);
  const l = colour(lossName, `WINLOSS ${lossName}`);
  if (w && l) {
    const lw = lum(w), ll = lum(l);
    const pct = (Math.abs(lw - ll) / Math.max(lw, ll)) * 100;
    const shown = `${pct.toFixed(1)}%`;
    if (pct <= 5) { winlossOk = true; console.log(`WINLOSS OK ${shown}`); }
    else {
      fail("WINLOSS", `|La - Lb| / max(La, Lb) <= 5% (${winName} vs ${lossName})`, `${shown} (L ${lw.toFixed(4)} ${hex(w)} vs ${ll.toFixed(4)} ${hex(l)})`);
      console.log(`WINLOSS FAILED ${shown}`);
    }
  } else console.log("WINLOSS FAILED unresolved");
}
process.exit(contrastOk && winlossOk ? 0 : 1);
