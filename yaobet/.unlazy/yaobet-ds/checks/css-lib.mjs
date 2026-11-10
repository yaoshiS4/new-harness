/* Shared helpers for the Wine-Gold checks.
 *
 * Target tree: the git top level of the current working directory (its built
 * .next/static CSS and its src/). Doc inputs (MAPPING.md, the DS and overlay
 * JSON, pins, pairs) come from the repo that holds this checks directory, so the
 * same scripts can be pointed at an older tree.
 *
 * CLI (used by the .sh wrappers; each prints "OK <id>" or "Fail: <id> | Expected: <A> | Got: <B>" lines):
 *   node css-lib.mjs themecolor <value>   layout themeColor = built --canvas = DS bg.page
 *   node css-lib.mjs tier                 the --wg-* tier rule over src/ (definition files)
 *   node css-lib.mjs newhex               colours on lines added since BASE_REF in the definition files
 *   node css-lib.mjs mirror               genplan.py mirrors of every pins.txt check row
 */

import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

export const DS_DIR = path.dirname(fileURLToPath(import.meta.url));
export const DS_ROOT = git(["-C", DS_DIR, "rev-parse", "--show-toplevel"]).trim();
export const TARGET = (() => {
  try {
    return git(["rev-parse", "--show-toplevel"]).trim();
  } catch {
    return process.cwd();
  }
})();
export const BASE_REF = "635a4dc";
export const DEFS = ["src/styles/tokens.css", "src/styles/themes.css", "src/styles/brands.css"];
export const WG = path.join(DS_ROOT, "docs/design/wine-gold");

export function git(args, cwd) {
  return execFileSync("git", args, { cwd: cwd ?? process.cwd(), encoding: "utf8", maxBuffer: 64 << 20, stdio: ["ignore", "pipe", "pipe"] });
}
/* A file as it was at BASE_REF, read from the doc repo. */
export const baseFile = (rel) => git(["-C", DS_ROOT, "show", `${BASE_REF}:${rel}`]);

let FAILS = 0;
let OKS = 0;
export const counts = () => ({ ok: OKS, fail: FAILS });
const flat = (s) => String(s).replace(/\s+/g, " ").trim().slice(0, 240);
export function fail(id, exp, got) {
  FAILS++;
  console.log(`Fail: ${id} | Expected: ${flat(exp)} | Got: ${flat(got)}`);
  return false;
}
export function ok(id) {
  OKS++;
  if (process.env.CSS_LIB_CLI) console.log(`OK ${id}`);
  return true;
}

/* ---------------------------------------------------------------- CSS parsing */

function stripComments(t) {
  let out = "";
  let i = 0;
  while (i < t.length) {
    const c = t[i];
    if (c === '"' || c === "'") {
      const j = endOfString(t, i);
      out += t.slice(i, j);
      i = j;
    } else if (c === "/" && t[i + 1] === "*") {
      const j = t.indexOf("*/", i + 2);
      const e = j < 0 ? t.length : j + 2;
      out += t.slice(i, e).replace(/[^\n]/g, " ");
      i = e;
    } else {
      out += c;
      i++;
    }
  }
  return out;
}
function endOfString(t, i) {
  const q = t[i];
  let k = i + 1;
  while (k < t.length && t[k] !== q && t[k] !== "\n") k += t[k] === "\\" ? 2 : 1;
  return Math.min(k + 1, t.length);
}
/* First index >= i of a char in `stops` at paren/bracket depth 0, outside strings; -1 if none. */
function scan(t, i, stops) {
  let d = 0;
  for (let k = i; k < t.length; k++) {
    const c = t[k];
    if (c === '"' || c === "'") { k = endOfString(t, k) - 1; continue; }
    if (c === "(" || c === "[") d++;
    else if (c === ")" || c === "]") d = Math.max(0, d - 1);
    else if (d === 0 && stops.includes(c)) return k;
  }
  return -1;
}
export function splitTop(s, sep = ",") {
  const out = [];
  let d = 0, cur = "";
  for (let k = 0; k < s.length; k++) {
    const c = s[k];
    if (c === '"' || c === "'") { const j = endOfString(s, k); cur += s.slice(k, j); k = j - 1; continue; }
    if (c === "(" || c === "[") d++;
    else if (c === ")" || c === "]") d--;
    if (c === sep && d === 0) { out.push(cur); cur = ""; } else cur += c;
  }
  out.push(cur);
  return out;
}
/* CSS Syntax 3 §4.3.7: "\" + 1-6 hex digits + one optional whitespace, or "\" + any other char. */
const codePoint = (hex) => {
  const cp = parseInt(hex, 16);
  return cp === 0 || cp > 0x10ffff || (cp >= 0xd800 && cp <= 0xdfff) ? "\uFFFD" : String.fromCodePoint(cp);
};
export const cssUnescape = (s) =>
  s.replace(/\\(?:([0-9a-fA-F]{1,6})(?:\r\n|[ \t\n\r\f])?|([^]))/g, (m, hex, ch) => (hex === undefined ? ch : codePoint(hex)));
/* Escapes are decoded last so escaped and plain spellings of a selector compare equal. Every escape is
 * first rewritten as exactly 6 hex digits with no terminator, so neither its terminating whitespace nor
 * an escaped space or combinator is touched by the whitespace and combinator normalisation. */
export const normSel = (s) =>
  s.replace(/\\(?:([0-9a-fA-F]{1,6})(?:\r\n|[ \t\n\r\f])?|([^]))/gu, (m, h, ch) => "\\" + (h ?? ch.codePointAt(0).toString(16)).padStart(6, "0"))
    .replace(/\s+/g, " ").replace(/\[\s*([\w-]+)\s*=\s*["']?([^"'\]]*?)["']?\s*\]/g, "[$1=$2]").replace(/\s*([>+~])\s*/g, "$1").trim()
    .replace(/\\([0-9a-fA-F]{6})/g, (m, h) => codePoint(h));

/* rules: [{ sel: [normalised selectors], ctx: [at-rule preludes], decls: [{ p, v, line }], line }] in source order. */
export function parseCss(src, file = "") {
  const t = stripComments(src);
  const nl = [];
  for (let k = 0; k < t.length; k++) if (t[k] === "\n") nl.push(k);
  const lineAt = (pos) => { let lo = 0, hi = nl.length; while (lo < hi) { const m = (lo + hi) >> 1; if (nl[m] < pos) lo = m + 1; else hi = m; } return lo + 1; };
  const rules = [];
  let i = 0;
  const ws = () => { while (i < t.length && /\s/.test(t[i])) i++; };
  function skipBlock() {
    let d = 1;
    while (i < t.length && d > 0) {
      const c = t[i];
      if (c === '"' || c === "'") { i = endOfString(t, i); continue; }
      if (c === "{") d++;
      else if (c === "}") d--;
      i++;
    }
  }
  function body(rule, ctx) {
    for (;;) {
      ws();
      if (i >= t.length) return;
      if (t[i] === "}") { i++; return; }
      const j = scan(t, i, "{;}");
      if (j < 0) { i = t.length; return; }
      const pre = t.slice(i, j).trim();
      if (t[j] === "{") {
        const at = i;
        i = j + 1;
        const sel = splitTop(pre).map(normSel);
        const child = { sel, ctx, decls: [], line: lineAt(at), file };
        rules.push(child);
        body(child, ctx);
        continue;
      }
      const c = pre.indexOf(":");
      if (c > 0) rule.decls.push({ p: pre.slice(0, c).trim(), v: pre.slice(c + 1).trim().replace(/\s*!important$/i, ""), line: lineAt(i) });
      i = t[j] === ";" ? j + 1 : j;
    }
  }
  function block(ctx) {
    for (;;) {
      ws();
      if (i >= t.length) return;
      if (t[i] === "}") { i++; return; }
      const j = scan(t, i, "{;}");
      if (j < 0) { i = t.length; return; }
      const pre = t.slice(i, j).trim();
      const at = i;
      if (t[j] === ";") { i = j + 1; continue; }
      if (t[j] === "}") { i = j + 1; return; }
      i = j + 1;
      if (pre.startsWith("@")) {
        const name = (pre.match(/^@([\w-]+)/) || [, ""])[1].toLowerCase();
        if (name === "font-face" || name === "property" || name === "page") {
          const r = { sel: ["@" + name + (name === "property" ? " " + pre.slice(9).trim() : "")], ctx, decls: [], line: lineAt(at), file };
          rules.push(r);
          body(r, ctx);
        } else if (name.endsWith("keyframes")) skipBlock();
        else block([...ctx, pre.replace(/\s+/g, " ").replace(/\s*:\s*/g, ":")]);
      } else {
        const r = { sel: splitTop(pre).map(normSel), ctx, decls: [], line: lineAt(at), file };
        rules.push(r);
        body(r, ctx);
      }
    }
  }
  block([]);
  return rules;
}

/* ---------------------------------------------------------------- built CSS */

export function builtCssFiles(root = TARGET) {
  const dir = path.join(root, ".next/static");
  const out = [];
  const walk = (d) => {
    for (const n of readdirSync(d).sort()) {
      const f = path.join(d, n);
      if (statSync(f).isDirectory()) walk(f);
      else if (n.endsWith(".css")) out.push(f);
    }
  };
  if (existsSync(dir)) walk(dir);
  return out;
}
export function loadBuilt(root = TARGET) {
  if (!existsSync(path.join(root, ".next/BUILD_ID"))) return null;
  const files = builtCssFiles(root);
  const rules = [];
  for (const f of files) rules.push(...parseCss(readFileSync(f, "utf8"), path.relative(root, f)));
  return { files, rules };
}
export const inMedia = (r) => r.ctx.some((c) => /^@(media|container)\b/i.test(c));

/* Custom properties that apply on <html> carrying the given attribute selectors, in cascade (source) order.
 * @supports and @layer blocks apply; @media and @container blocks do not. */
export function scopeMap(rules, selectors, { media = null } = {}) {
  const want = new Set(selectors);
  const m = new Map();
  for (const r of rules) {
    if (media ? !r.ctx.some((c) => c.includes(media)) : inMedia(r)) continue;
    if (!r.sel.some((s) => want.has(s))) continue;
    for (const d of r.decls) if (d.p.startsWith("--")) m.set(d.p, d.v);
  }
  return m;
}
/* next/font loader variables (".<hash>_variable { --font-x: ... }"). */
export function loaderMap(rules) {
  const m = new Map();
  for (const r of rules) if (r.sel.length === 1 && /^\.[\w-]*variable$/i.test(r.sel[0])) for (const d of r.decls) if (d.p.startsWith("--")) m.set(d.p, d.v);
  return m;
}
export const SCOPE = {
  base: [":root", "[data-brand=yaobet]"],
  emerald: [":root", "[data-brand=emerald]"],
  obsidian: [":root", "[data-theme=obsidian]", "[data-brand=yaobet]"],
};

export class Unresolved extends Error {}
function matchParen(s, open) {
  let d = 0;
  for (let k = open; k < s.length; k++) {
    if (s[k] === "(") d++;
    else if (s[k] === ")" && --d === 0) return k;
  }
  return -1;
}
export function substitute(v, map, loader, seen = new Set()) {
  let out = "", i = 0;
  for (;;) {
    const k = v.indexOf("var(", i);
    if (k < 0) return out + v.slice(i);
    out += v.slice(i, k);
    const end = matchParen(v, k + 3);
    if (end < 0) throw new Unresolved(`unbalanced var() in ${v}`);
    const inner = v.slice(k + 4, end);
    const parts = splitTop(inner);
    const name = parts[0].trim();
    const fb = parts.length > 1 ? parts.slice(1).join(",").trim() : undefined;
    if (map.has(name) || loader?.has(name)) out += resolveVar(name, map, loader, seen);
    else throw new Unresolved(fb === undefined ? name : `${name} (only its fallback is declared)`);
    i = end + 1;
  }
}
export function resolveVar(name, map, loader, seen = new Set()) {
  if (seen.has(name)) throw new Unresolved(`${name} (cycle)`);
  const v = map.has(name) ? map.get(name) : loader?.get(name);
  if (v === undefined) throw new Unresolved(name);
  return substitute(v, map, loader, new Set([...seen, name])).trim();
}
/* Resolved value or { error } without throwing. */
export function tryResolve(name, map, loader) {
  try {
    return { value: resolveVar(name, map, loader) };
  } catch (e) {
    return { error: e instanceof Unresolved ? `unresolved ${e.message}` : String(e) };
  }
}

/* ---------------------------------------------------------------- colour and value canon */

const NAMED = { transparent: [0, 0, 0, 0], white: [255, 255, 255, 1], black: [0, 0, 0, 1] };
function hsl2rgb(h, s, l) {
  h = ((h % 360) + 360) % 360; s /= 100; l /= 100;
  const f = (n) => { const k = (n + h / 30) % 12; return l - s * Math.min(l, 1 - l) * Math.max(-1, Math.min(k - 3, 9 - k, 1)); };
  return [f(0) * 255, f(8) * 255, f(4) * 255];
}
/* [r, g, b, a] (0-255, 0-1) for one colour token, or null. */
export function parseColour(tok) {
  const s = String(tok).trim().toLowerCase();
  if (NAMED[s]) return NAMED[s];
  let m = s.match(/^#([0-9a-f]{3,8})$/);
  if (m) {
    let h = m[1];
    if (![3, 4, 6, 8].includes(h.length)) return null;
    if (h.length <= 4) h = [...h].map((c) => c + c).join("");
    const n = (i) => parseInt(h.slice(i, i + 2), 16);
    return [n(0), n(2), n(4), h.length === 8 ? n(6) / 255 : 1];
  }
  m = s.match(/^(rgba?|hsla?)\((.*)\)$/);
  if (!m) return null;
  const args = m[2].replace(/\s*\/\s*/, ",").split(/\s*,\s*|\s+/).filter(Boolean);
  if (args.length < 3 || args.some((a) => !/^[-+]?(\d*\.)?\d+(%|deg)?$/.test(a))) return null;
  const num = (a) => parseFloat(a);
  const alpha = args[3] === undefined ? 1 : args[3].endsWith("%") ? num(args[3]) / 100 : num(args[3]);
  if (m[1].startsWith("rgb")) return [...args.slice(0, 3).map((a) => (a.endsWith("%") ? (num(a) * 255) / 100 : num(a))), alpha];
  return [...hsl2rgb(num(args[0]), num(args[1]), num(args[2])), alpha];
}
const fmtC = ([r, g, b, a]) => `c(${Math.round(r)},${Math.round(g)},${Math.round(b)},${Math.round(a * 255)})`;
const unC = (t) => { const n = t.slice(2, -1).split(",").map(Number); return [n[0], n[1], n[2], n[3] / 255]; };
const COLOUR_RE = /#[0-9a-f]{3,8}(?![0-9a-z_-])|\b(?:rgba?|hsla?)\([^()]*\)|\b(?:transparent|white|black)\b/gi;
function mix(a, pa, b, pb) {
  if (pa === undefined && pb === undefined) pa = pb = 50;
  else if (pa === undefined) pa = 100 - pb;
  else if (pb === undefined) pb = 100 - pa;
  const sum = pa + pb;
  if (sum <= 0) return null;
  const wa = pa / sum, wb = pb / sum;
  const al = a[3] * wa + b[3] * wb;
  const ch = (k) => (al === 0 ? 0 : (a[k] * a[3] * wa + b[k] * b[3] * wb) / al);
  return [ch(0), ch(1), ch(2), al * Math.min(1, sum / 100)];
}
export function canon(v) {
  let s = String(v).trim().replace(/\s*!important$/i, "").toLowerCase();
  s = s.replace(/["']/g, "");
  s = s.replace(COLOUR_RE, (t) => { const c = parseColour(t); return c ? fmtC(c) : t; });
  s = s.replace(/\s+/g, " ").replace(/\s*([,()/])\s*/g, "$1");
  const MIX = /color-mix\(in srgb,(c\([^)]*\)) ?(?:([\d.]+)%)?,(c\([^)]*\)) ?(?:([\d.]+)%)?\)/;
  for (let m; (m = s.match(MIX)); ) {
    const r = mix(unC(m[1]), m[2] === undefined ? undefined : +m[2], unC(m[3]), m[4] === undefined ? undefined : +m[4]);
    if (!r) break;
    s = s.replace(m[0], fmtC(r));
  }
  s = s.replace(/(^|[^\w.#-])(-?)(\d*\.?\d+)(ms|s|px|em|rem|%|deg|vw|vh|fr)?(?![\w.])/g, (all, pre, sign, digits, unit = "") => {
    let n = parseFloat(sign + digits);
    if (unit === "s") { n *= 1000; unit = "ms"; }
    if (n === 0 && ["px", "em", "rem"].includes(unit)) unit = "";
    let str = String(+n.toFixed(4));
    str = str.replace(/^(-?)0\./, "$1.");
    return pre + str + unit;
  });
  s = stripCalc(s);
  return s;
}
/* clamp(a,calc(b),c) == clamp(a,b,c): drop calc() wrappers that are whole arguments of clamp/min/max. */
function stripCalc(s) {
  for (let guard = 0; guard < 50; guard++) {
    const stack = [];
    let done = false;
    for (let k = 0; k < s.length && !done; k++) {
      if (s[k] === "(") {
        const name = (s.slice(0, k).match(/([\w-]*)$/) || ["", ""])[1];
        stack.push(name);
        const outer = stack[stack.length - 2];
        const start = k - 4;
        if (name === "calc" && ["clamp", "min", "max"].includes(outer) && [",", "("].includes(s[start - 1])) {
          const end = matchParen(s, k);
          if (end > 0 && [",", ")"].includes(s[end + 1])) {
            s = s.slice(0, start) + s.slice(k + 1, end) + s.slice(end + 1);
            done = true;
          }
        }
      } else if (s[k] === ")") stack.pop();
    }
    if (!done) break;
  }
  return s;
}
/* All colours in a value, as canon tokens. */
export const colours = (v) => canon(v).match(/c\(\d+,\d+,\d+,\d+\)/g) || [];
export const colourOf = (v) => { const c = canon(v); return /^c\(\d+,\d+,\d+,\d+\)$/.test(c) ? unC(c) : null; };
export function firstFamily(v) {
  let f = splitTop(String(v))[0].trim().replace(/^["']|["']$/g, "").trim();
  f = f.replace(/^__(.+?)_[0-9a-f]{6,}$/i, "$1").replace(/^__/, "").replace(/_/g, " ");
  return f.toLowerCase();
}

/* ---------------------------------------------------------------- DS + overlay JSON */

function walkTokens(o, p, out) {
  if (o && typeof o === "object" && "$value" in o) { out.set(p.join("."), o); return; }
  if (o && typeof o === "object") for (const [k, v] of Object.entries(o)) if (!k.startsWith("$")) walkTokens(v, [...p, k], out);
}
let _ds = null;
/* { ds: Map(path -> token), ov: Map(path -> token), all: Map } ; DS refs drop the category prefix. */
export function tokens() {
  if (_ds) return _ds;
  const dsj = JSON.parse(readFileSync(path.join(WG, "design-tokens.all.json"), "utf8"));
  const ovj = JSON.parse(readFileSync(path.join(WG, "overlay.proposal.json"), "utf8"));
  const ds = new Map(), ov = new Map();
  for (const [cat, body] of Object.entries(dsj)) if (!cat.startsWith("$")) walkTokens(body, [], ds);
  walkTokens(ovj, [], ov);
  const all = new Map([...ds, ...ov]);
  _ds = { ds, ov, all };
  return _ds;
}
export function dsValue(p, seen = new Set()) {
  const { all } = tokens();
  const t = all.get(p);
  if (!t) throw new Unresolved(`DS token ${p}`);
  if (seen.has(p)) throw new Unresolved(`DS cycle ${p}`);
  return String(t.$value).replace(/\{([^}]+)\}/g, (m, r) => dsValue(r, new Set([...seen, p])));
}
export const dsRef = (p) => { const m = String(tokens().all.get(p)?.$value ?? "").match(/^\{([^}]+)\}$/); return m ? m[1] : null; };
/* A short DS reference as written in MAPPING ("surface.3", "gold.400", "role h4") -> full token paths. */
export function dsLookup(short, { overlayOnly = false } = {}) {
  const { ds, ov } = tokens();
  const s = short.trim().replace(/\s+/g, ".");
  const pool = overlayOnly ? [...ov.keys()] : [...ov.keys(), ...ds.keys()];
  const hit = pool.filter((k) => k === s || k.endsWith("." + s));
  return [...new Set(hit)];
}
/* --wg-color-* name of a primitive.color path (MAPPING.md:16). */
export const wgColourName = (p) => "--wg-color-" + p.replace(/^primitive\.color\./, "").replace(/^alpha\./, "").split(".").join("-");

/* ---------------------------------------------------------------- CLI */

function cliThemeColor(val) {
  const built = loadBuilt();
  if (!built) return fail("themecolor-build", ".next/BUILD_ID", "missing");
  const m = scopeMap(built.rules, SCOPE.base);
  const r = tryResolve("--canvas", m, loaderMap(built.rules));
  if (r.error) return fail("themecolor-canvas", "--canvas resolves in the built CSS", r.error);
  const page = dsValue("semantic.color.bg.page");
  canon(val) === canon(r.value) ? ok("themecolor-built") : fail("themecolor-built", `themeColor = built --canvas ${r.value}`, val);
  canon(val) === canon(page) ? ok("themecolor-page-primitive") : fail("themecolor-page-primitive", `themeColor = DS bg.page ${page}`, val);
}

const COMPONENT_34 = /^--(card-bg|button-secondary-text|control-checked-[\w-]+|input-[\w-]+|tab-text-[\w-]+|odds-(up|down)|vip-bg|vip-header-bg|(modal|toast|tooltip)-(border|meta)|feedback-bg-paused)$/;
function srcFiles(dir, exts) {
  const out = [];
  const walk = (d) => {
    for (const n of readdirSync(d).sort()) {
      const f = path.join(d, n);
      if (statSync(f).isDirectory()) walk(f);
      else if (exts.some((e) => n.endsWith(e))) out.push(f);
    }
  };
  if (existsSync(dir)) walk(dir);
  return out;
}
function cliTier() {
  const rel = (f) => path.relative(TARGET, f);
  const css = srcFiles(path.join(TARGET, "src"), [".css"]);
  let wgDecl = 0, compSeen = 0;
  for (const f of css) {
    const r = rel(f);
    for (const rule of parseCss(readFileSync(f, "utf8"), r)) {
      for (const d of rule.decls) {
        if (d.p.startsWith("--wg-")) {
          wgDecl++;
          const where = `${r}:${d.line}`;
          const rootOk = r === "src/styles/tokens.css" && rule.sel.length === 1 && rule.sel[0] === ":root" && rule.ctx.length === 0;
          rootOk ? ok(`tier-wg-scope ${d.p}`) : fail(`tier-wg-scope ${where}`, `${d.p} declared only in the :root of src/styles/tokens.css`, `${rule.ctx.join(" ")} ${rule.sel.join(",")}`);
          const reads = d.v.match(/var\(\s*--[\w-]+/g) || [];
          const bad = reads.filter((x) => !/^var\(\s*--font-[a-z0-9-]+$/.test(x));
          bad.length === 0 ? ok(`tier-wg-literal ${d.p}`) : fail(`tier-wg-literal ${where}`, `${d.p} is a literal or a next/font --font-* loader var`, d.v);
        }
        if (COMPONENT_34.test(d.p) && DEFS.includes(r)) {
          compSeen++;
          /var\(\s*--wg-/.test(d.v) ? fail(`tier-component ${r}:${d.line}`, `${d.p} reads a semantic name, never --wg-*`, d.v) : ok(`tier-component ${d.p}`);
        }
      }
    }
  }
  const ts = srcFiles(path.join(TARGET, "src"), [".ts", ".tsx", ".js", ".jsx", ".mjs"]);
  for (const f of ts) {
    const lines = readFileSync(f, "utf8").split("\n");
    lines.forEach((l, k) => { if (/["'`]--wg-[\w-]+["'`]\s*:|--wg-[\w-]+\s*:/.test(l)) fail(`tier-wg-scope ${rel(f)}:${k + 1}`, "no --wg-* declared outside the :root of tokens.css", l); });
  }
  console.log(`tier: ${wgDecl} --wg-* declarations, ${compSeen} component declarations`);
  ok("tier-scan");
}

function colourSet(text) {
  const out = new Set();
  const re = /(?<!&)#[0-9a-fA-F]{3,8}(?![0-9A-Za-z_-])|\b(?:rgba?|hsla?)\(\s*[-+]?\.?\d[^()]*\)/g;
  for (const m of String(text).matchAll(re)) { const c = parseColour(m[0]); if (c) out.add(fmtC(c)); }
  return out;
}
function cliNewhex() {
  const allowed = new Set();
  for (const f of ["design-tokens.all.json", "overlay.proposal.json"]) {
    for (const c of colourSet(readFileSync(path.join(WG, f), "utf8"))) allowed.add(c);
  }
  for (const d of DEFS) for (const c of colourSet(baseFile(d))) allowed.add(c);
  allowed.size > 0 ? ok("newhex-union") : fail("newhex-union", "a non-empty colour union", "0");
  const diff = git(["diff", "-U0", "--no-color", BASE_REF, "--", ...DEFS], TARGET);
  let file = "", nline = 0, added = 0;
  for (const l of diff.split("\n")) {
    if (l.startsWith("+++ ")) { file = l.slice(4).replace(/^b\//, ""); continue; }
    const h = l.match(/^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
    if (h) { nline = +h[1]; continue; }
    if (l.startsWith("+") && !l.startsWith("+++")) {
      added++;
      const re = /(?<!&)#[0-9a-fA-F]{3,8}(?![0-9A-Za-z_-])|\b(?:rgba?|hsla?)\(\s*[-+]?\.?\d[^()]*\)/g;
      for (const m of l.slice(1).matchAll(re)) {
        const c = parseColour(m[0]);
        if (!c) { fail(`newhex ${file}:${nline}`, "a parsable colour", m[0]); continue; }
        allowed.has(fmtC(c)) ? ok(`newhex ${file}:${nline}`) : fail(`newhex ${file}:${nline}`, "a DS, overlay or 635a4dc colour", m[0]);
      }
      nline++;
    }
  }
  console.log(`newhex: ${added} added lines, ${allowed.size} allowed colours`);
}

/* Pin rows -> genplan.py mirror range and the key-literal extractor for the new check line(s). */
const MIRRORS = {
  ".unlazy/yaobet-rebuild/checks/F1.sh:7": [[450, 450], (t) => [t.match(/\beq\s+(\d+)/)?.[1]]],
  ".unlazy/yaobet-rebuild/checks/F1.sh:12": [[455, 455], (t) => [t.match(/\beq\s+(\d+)/)?.[1]]],
  ".unlazy/yaobet-rebuild/checks/built-css.sh:9": [[932, 932], (t) => [t.match(/"(--canvas:[^"]*)"/)?.[1]]],
  ".unlazy/yaobet-rebuild/checks/built-css.sh:13": [[922, 928], (t) => t.match(/\b[0-9a-f]{64}\b/g) || [undefined]],
  ".unlazy/yaobet-rebuild/checks/U1.sh:10-11": [[527, 528], (t) => [...t.matchAll(/^hasre\s+\S+\s+'([^']*)'/gm)].map((m) => m[1])],
  ".unlazy/yaobet-rebuild/checks/I1.sh:10": [[761, 761], (t) => [t.match(/^html\s+\S+\s+\S+\s+'([^']*)'/m)?.[1]]],
  ".unlazy/yaobet-rebuild/checks/I1.sh:13": [[764, 764], (t) => [t.match(/^html\s+\S+\s+\S+\s+'([^']*)'/m)?.[1]]],
  ".unlazy/yaobet-rebuild/checks/F5.sh:7": [[747, 747], (t) => [t.match(/\beq\s+(\d+)/)?.[1]]],
  ".unlazy/yaobet-rebuild/checks/S3.sh:7": [[565, 565], (t) => [t.match(/^(eq\s+\S+\s+"[^"]*")/m)?.[1]]],
};
function hunks(file) {
  const d = git(["diff", "-U0", "--no-color", BASE_REF, "--", file], TARGET);
  const out = [];
  for (const m of d.matchAll(/^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@/gm)) {
    const a = +m[1], b = m[2] === undefined ? 1 : +m[2], c = +m[3], dd = m[4] === undefined ? 1 : +m[4];
    out.push({ a, aEnd: b ? a + b - 1 : a, c, cEnd: c + dd - 1, newLen: dd });
  }
  return out;
}
function boxArrays(text) {
  /* [{ id, width, start, end, literal }] for every "<width>": [ ... ] array in boxes.json. */
  const lines = text.split("\n");
  const out = [];
  let id = null;
  for (let k = 0; k < lines.length; k++) {
    const idm = lines[k].match(/^\s{4}"([^"]+)":\s*\{/);
    if (idm) id = idm[1];
    const w = lines[k].match(/^\s*"(\d{3,4})":\s*\[/);
    if (!w) continue;
    let e = k, buf = lines[k];
    while (!buf.includes("]") && e + 1 < lines.length) buf += lines[++e];
    const nums = buf.slice(buf.indexOf("[") + 1, buf.indexOf("]")).split(",").map((x) => x.trim()).filter(Boolean);
    out.push({ id, width: w[1], start: k + 1, end: e + 1, literal: `[${nums.join(", ")}]` });
  }
  return out;
}
function cliMirror() {
  const pins = readFileSync(path.join(DS_DIR, "pins.txt"), "utf8").split("\n").filter(Boolean);
  const GEN = ".unlazy/yaobet-rebuild/genplan.py";
  const genLines = readFileSync(path.join(TARGET, GEN), "utf8").split("\n");
  const genHunks = hunks(GEN);
  const genRange = (pred) => genHunks.filter(pred).map((h) => genLines.slice(h.c - 1, h.c - 1 + h.newLen).join("\n")).join("\n");
  let n = 0;
  for (const row of pins) {
    const m = row.match(/^(.+):(\d+)(?:-(\d+))?$/);
    if (!m) { fail(`mirror-row ${row}`, "<path>:<start>[-<end>]", row); continue; }
    const [, file, s, e] = m;
    if (file === GEN) continue;
    /* a11-allow.txt is PM-filled after review; genplan.py writes only its header. */
    if (file.endsWith("/a11-allow.txt")) continue;
    const a = +s, b = +(e || s);
    let literals = [], target = null;
    if (file.endsWith("/boxes.json")) {
      const text = readFileSync(path.join(TARGET, file), "utf8");
      const hs = hunks(file).filter((h) => h.a >= a && h.aEnd <= b && h.newLen > 0);
      if (!hs.length) { fail(`mirror ${row}`, "a changed boxes.json hunk inside the pin", "no hunk"); continue; }
      const arrays = boxArrays(text).filter((x) => hs.some((h) => x.start <= h.cEnd && x.end >= h.c));
      literals = arrays.map((x) => x.literal);
      target = genRange((h) => h.a >= 989 && h.aEnd <= 998);
      if (!literals.length) { fail(`mirror ${row}`, "a re-pinned box array", "none"); continue; }
    } else {
      const spec = MIRRORS[row];
      if (!spec) { fail(`mirror ${row}`, "a known check pin", "no mirror rule"); continue; }
      /* Any hunk overlapping the pinned old range counts (a change to U1.sh:11 alone is still the :10-11 pin). */
      const hs = hunks(file).filter((x) => x.a <= b && x.aEnd >= a && x.newLen > 0);
      if (!hs.length) { fail(`mirror ${row}`, `a hunk overlapping ${a}-${b} in ${file}`, "pin unchanged"); continue; }
      const fileLines = readFileSync(path.join(TARGET, file), "utf8").split("\n");
      literals = hs.flatMap((h) => spec[1](fileLines.slice(h.c - 1, h.c - 1 + h.newLen).join("\n")));
      const [ga, gb] = spec[0];
      const gs = genHunks.filter((x) => x.a <= gb && x.aEnd >= ga && x.newLen > 0);
      if (!gs.length) { fail(`mirror ${row}`, `a genplan.py hunk overlapping ${ga}-${gb}`, "none"); continue; }
      target = gs.map((g) => genLines.slice(g.c - 1, g.c - 1 + g.newLen).join("\n")).join("\n");
    }
    for (const lit of literals) {
      n++;
      if (lit === undefined || lit === "") { fail(`mirror ${row}`, "a key literal on the new check line", "none found"); continue; }
      /* Integers match on digit boundaries, so "4" never matches inside "245". */
      const found = target && (/^\d+$/.test(lit) ? new RegExp(`(^|[^0-9])${lit}([^0-9]|$)`).test(target) : target.includes(lit));
      found ? ok(`mirror ${row} ${lit.slice(0, 40)}`) : fail(`mirror ${row}`, `'${lit}' in the genplan.py new-side range`, "absent");
    }
  }
  console.log(`mirror: ${n} literals`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  process.env.CSS_LIB_CLI = "1";
  const [cmd, ...rest] = process.argv.slice(2);
  try {
    if (cmd === "themecolor") cliThemeColor(rest[0] ?? "");
    else if (cmd === "tier") cliTier();
    else if (cmd === "newhex") cliNewhex();
    else if (cmd === "mirror") cliMirror();
    else { console.log(`Fail: css-lib | Expected: themecolor|tier|newhex|mirror | Got: ${cmd ?? "none"}`); process.exit(2); }
  } catch (e) {
    console.log(`Fail: css-lib-${cmd} | Expected: no error | Got: ${flat(e.message)}`);
    process.exit(2);
  }
  process.exit(counts().fail ? 1 : 0);
}
