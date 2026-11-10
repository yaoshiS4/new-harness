#!/usr/bin/env node
/* Token parity: every MAPPING.md §2-§10 table data row and every overlay token,
 * checked against the built .next/static CSS of the tree in the cwd.
 *
 * Names resolve through the var() chain in cascade order: :root (tokens.css), then
 * [data-brand="yaobet"] (brands.css); [data-theme] is not applied (D-DS10), except
 * for the obsidian check. Each row is handled by an explicit class; a row that fits
 * no class FAILS. Prints one count line per section, OVERLAY, OBSIDIAN and WG-COLOR
 * lines, then `PARITY OK N/N` (N = data rows + overlay tokens) as the last line. */

import { readFileSync } from "node:fs";
import path from "node:path";
import {
  BASE_REF, SCOPE, TARGET, WG, baseFile, canon, colourOf, colours, dsLookup, dsRef, dsValue, fail as report,
  firstFamily, loadBuilt, loaderMap, parseColour, parseCss, scopeMap, substitute, tokens, tryResolve, wgColourName,
} from "./css-lib.mjs";

const built = loadBuilt();
if (!built) {
  console.log(`Fail: parity-build | Expected: ${path.join(TARGET, ".next/BUILD_ID")} (run npm run build) | Got: missing`);
  console.log("PARITY FAILED no build");
  process.exit(1);
}
const R = built.rules;
const LOADER = loaderMap(R);
const BASE = scopeMap(R, SCOPE.base);
const res = (name, map = BASE) => tryResolve(name, map, LOADER);

/* The tree at BASE_REF, read from the doc repo: tokens < themes < brands (F1.sh:16 import order). */
const baseRules = parseCss(["src/styles/tokens.css", "src/styles/themes.css", "src/styles/brands.css"].map(baseFile).join("\n"));
const BASE_OLD = scopeMap(baseRules, SCOPE.base);
const resOld = (name) => tryResolve(name, BASE_OLD, LOADER);

/* ---------------------------------------------------------------- MAPPING.md tables */

const MD = readFileSync(path.join(WG, "MAPPING.md"), "utf8").split("\n");
const splitCells = (line) => {
  const out = [];
  let cur = "", tick = false;
  for (const ch of line.trim().replace(/^\|/, "").replace(/\|$/, "")) {
    if (ch === "`") tick = !tick;
    if (ch === "|" && !tick) { out.push(cur.trim()); cur = ""; } else cur += ch;
  }
  out.push(cur.trim());
  return out;
};
const tables = [];
{
  let sec = 0, cur = null;
  MD.forEach((line, k) => {
    const h = line.match(/^## (\d+)\./);
    if (h) sec = +h[1];
    if (/^\|/.test(line) && sec >= 2 && sec <= 10) {
      if (!cur) { cur = { sec, header: splitCells(line), rows: [], sep: false, line: k + 1 }; tables.push(cur); }
      else if (!cur.sep && /^\|[-| :]+\|$/.test(line.trim())) cur.sep = true;
      else cur.rows.push({ sec, cells: splitCells(line), line: k + 1, text: line });
    } else cur = null;
  });
}
const ticks = (s) => [...String(s).matchAll(/`(--[\w-]+)`/g)].map((m) => m[1]);
const bare = (s) => String(s).replace(/`/g, "").trim();
const genericTables = tables.filter((t) => t.header[0].startsWith("Current token") && t.header.includes("Maps to") && t.header.includes("New"));

/* OV abbreviation in a "Maps to" cell -> overlay token paths. "OV role h4" is that role's size. */
function ovPaths(maps) {
  const m = String(maps).match(/\bOV (role [\w-]+|[\w.-]+(?: \/ [\w.-]+)*)/);
  if (!m) return [];
  if (m[1].startsWith("role ")) return [`semantic.type.role.${m[1].slice(5)}.size`];
  const parts = m[1].split(" / ");
  const out = [];
  let prev = null;
  for (const p of parts) {
    let full = p;
    if (prev) { const ps = prev.split("."), qs = p.split("."); if (qs.length < ps.length) full = [...ps.slice(0, ps.length - qs.length), ...qs].join("."); }
    const hit = dsLookup(full, { overlayOnly: true });
    out.push(hit.length === 1 ? hit[0] : `?${full}`);
    prev = full;
  }
  return out;
}
const dsCite = (maps) => { const m = String(maps).match(/\bDS ([\w.-]+)/); if (!m) return null; const hit = dsLookup(m[1]); return hit.length === 1 ? hit[0] : null; };

/* Indexes from the generic tables: overlay path -> names, DS path -> names, MAPPING semantic name -> first current name. */
const ovIndex = new Map(), dsIndex = new Map(), semIndex = new Map();
for (const t of genericTables) for (const r of t.rows) {
  const [c0, , maps] = r.cells;
  let name = ticks(c0)[0];
  if (!name && /\(none\)/.test(c0)) name = (String(maps).match(/->\s*`(--[\w-]+)`/) || [])[1];
  if (!name) continue;
  for (const p of ovPaths(maps)) if (!p.startsWith("?")) ovIndex.set(p, [...(ovIndex.get(p) || []), name]);
  const d = dsCite(maps);
  if (d) dsIndex.set(d, [...(dsIndex.get(d) || []), name]);
  for (const s of ticks(maps)) if (!semIndex.has(s)) semIndex.set(s, ticks(c0)[0]);
}

/* ---------------------------------------------------------------- overlay tokens */

const EXPLICIT = {
  "primitive.color.red.300": ["--wg-color-red-300"],
  "semantic.color.text.muted-raised": ["--fg-muted-raised"],
  "semantic.color.feedback.paused": ["--status-paused-fg"],
  "semantic.color.feedback.tint.paused": ["--status-paused-bg"],
  "semantic.color.action.secondary.text": ["--accent-secondary-fg"],
};
/* ADR-003 §3.4 and MAPPING names for an overlay token (MAPPING.md:38 grammar for the non-colour ones). */
export function ovCandidates(p) {
  const names = new Set(EXPLICIT[p] || []);
  if (p.startsWith("component.color.")) names.add("--" + p.slice(16).split(".").join("-"));
  for (const n of ovIndex.get(p) || []) names.add(n);
  if (/^(semantic|component|primitive)\.color\./.test(p)) return [...names];
  let m;
  if ((m = p.match(/^semantic\.type\.role\.([\w-]+)\.(family|size|leading|weight)$/))) names.add(`--type-${m[1]}-${m[2]}`);
  if (p === "semantic.type.weight.strong") names.add("--weight-strong");
  if ((m = p.match(/^semantic\.motion\.duration\.([\w-]+)$/))) { names.add(`--dur-${m[1]}`); names.add(`--motion-duration-${m[1]}`); }
  if ((m = p.match(/^semantic\.motion\.easing\.([\w-]+)$/))) names.add(`--ease-${m[1]}`);
  if ((m = p.match(/^semantic\.elevation\.level\.(\d)\.surface$/))) names.add(`--elevation-${m[1]}-surface`);
  if ((m = p.match(/^semantic\.radius\.([\w-]+)$/))) names.add(`--radius-${m[1]}`);
  if ((m = p.match(/^semantic\.spacing\.(.+)$/))) {
    const s = m[1];
    if (/^space\.\d+$/.test(s)) names.add(`--space-${s.split(".")[1]}`);
    else names.add("--" + s.split(".").join("-"));
  }
  const ref = dsRef(p);
  if (ref) for (const n of dsIndex.get(ref) || []) names.add(n);
  return [...names];
}
const sameValue = (type, got, exp) => (type === "fontFamily" ? firstFamily(got) === firstFamily(exp) : canon(got) === canon(exp));

const { ov } = tokens();
const ovResult = new Map();
for (const [p, tok] of ov) {
  const id = `overlay ${p}`;
  let exp;
  try { exp = dsValue(p); } catch (e) { ovResult.set(p, report(id, "a resolvable overlay $value", e.message)); continue; }
  const cands = ovCandidates(p);
  const declared = cands.filter((n) => BASE.has(n));
  if (!declared.length) { ovResult.set(p, report(id, `declared as one of ${cands.join(" ") || "(no name)"} = ${exp}`, "none declared")); continue; }
  let pass = true;
  for (const n of declared) {
    const r = res(n);
    if (r.error) { pass = report(`${id} ${n}`, exp, r.error); continue; }
    if (!sameValue(tok.$type, r.value, exp)) pass = report(`${id} ${n}`, exp, r.value);
  }
  ovResult.set(p, pass);
}

/* ---------------------------------------------------------------- row classes */

function newClass(newc, now, maps) {
  const lead = newc.split(/\s+/)[0];
  if (/^retired\b/i.test(maps)) {
    if (parseColour(lead)) return { kind: "colour", value: lead, note: newc.slice(lead.length).trim() };
    if (lead === "none") return { kind: "canon", value: "none" };
    const prim = dsLookup(lead).filter((p) => p.startsWith("primitive.color."));
    if (prim.length === 1) return { kind: "colour", value: dsValue(prim[0]), note: newc.slice(lead.length).trim() };
    return null;
  }
  if (newc === "composite") return { kind: "composite" };
  if (/\bkeep\b/i.test(maps) && canon(newc) === canon(now)) return { kind: "keep" };
  if (/^\d+-\d+px$/.test(newc)) {
    const p = ovPaths(maps)[0];
    return p && !p.startsWith("?") ? { kind: "canon", value: dsValue(p) } : null;
  }
  let m;
  if ((m = newc.match(/^([\w.]+) -> ([\w.]+)$/))) {
    const pick = (s) => dsLookup(s).filter((p) => p.startsWith("primitive.color."));
    const a = pick(m[1]), b = pick(m[2]);
    return a.length === 1 && b.length === 1 ? { kind: "stops", value: [dsValue(a[0]), dsValue(b[0])] } : null;
  }
  if (/family\.|--type-family-/.test(maps) && /^[A-Za-z][A-Za-z ]+$/.test(newc)) return { kind: "family", value: newc };
  if (/^\([\d.,\s]+\)$/.test(newc)) return { kind: "canon", value: `cubic-bezier${newc}` };
  if (parseColour(newc)) return { kind: "colour", value: newc };
  if (/^[-\w.%#(), /'"]+$/.test(newc)) return { kind: "canon", value: newc };
  return null;
}
function judge(id, cls, got, oldValue) {
  const show = (v) => (Array.isArray(v) ? v.join(" -> ") : v);
  switch (cls.kind) {
    case "composite": return true;
    case "keep": return canon(got) === canon(oldValue) ? true : report(id, `${BASE_REF} value ${oldValue}`, got);
    case "family": return firstFamily(got) === cls.value.toLowerCase() ? true : report(id, `family ${cls.value}`, firstFamily(got));
    case "stops": { const g = colours(got), e = cls.value.map(canon); return g.length === e.length && g.every((c, k) => c === e[k]) ? true : report(id, `colour stops ${show(cls.value)}`, got); }
    case "colour": {
      const e = canon(cls.value), cs = colours(got);
      const okv = canon(got) === e || (/gradient\(/.test(got) && cs.length > 0 && cs.every((c) => c === e));
      return okv ? true : report(id, cls.value, got);
    }
    default: return canon(got) === canon(cls.value) ? true : report(id, cls.value, got);
  }
}

const baseTypo = (file) => parseCss(baseFile(`src/styles/${file}`));
const mediaPreludes = new Set(R.flatMap((r) => r.ctx));

function genericRow(r) {
  const [c0, nowRaw, maps, newRaw] = r.cells;
  const now = bare(nowRaw), newc = bare(newRaw);
  const id = `MAPPING.md:${r.line}`;
  /* property rows: `letter-spacing` typography.css:47 */
  let m = bare(c0).match(/^([a-z-]+) ([\w-]+\.css):(\d+)$/);
  if (m) {
    const [, prop, file, ln] = m;
    const rule = baseTypo(file).find((x) => x.decls.some((d) => d.line === +ln));
    if (!rule) return report(id, `a declaration at ${file}:${ln} in ${BASE_REF}`, "none");
    const oldDecl = rule.decls.find((d) => d.line === +ln);
    const sels = new Set(rule.sel);
    const cls = /\bkeep\b/i.test(maps) && canon(newc) === canon(now) ? { kind: "canon", value: oldDecl.v } : newClass(newc, now, maps);
    if (!cls) return report(id, "a classifiable New cell", newc);
    const hits = R.filter((x) => !x.ctx.some((c) => /^@media/.test(c)) && x.sel.some((s) => sels.has(s)))
      .flatMap((x) => x.decls.filter((d) => d.p === prop || d.p.startsWith(prop + "-")));
    if (!hits.length) return report(id, `${prop}* on ${[...sels].join(",")} = ${newc}`, "no declaration");
    let pass = true;
    for (const d of hits) {
      let v;
      try { v = substitute(d.v, BASE, LOADER); } catch (e) { pass = report(id, newc, `unresolved ${e.message}`); continue; }
      if (!judge(`${id} ${d.p}`, cls, v)) pass = false;
    }
    return pass;
  }
  /* motion.css:16-18 (reduced motion): every duration token is 0 under prefers-reduced-motion */
  if (/^motion\.css:\d+/.test(bare(c0))) {
    const names = [...BASE.keys()].filter((n) => /^--(dur|motion-duration)-/.test(n));
    const reduced = new Map([...BASE, ...scopeMap(R, [":root"], { media: "prefers-reduced-motion:reduce" })]);
    let pass = names.length > 0 || report(id, "duration tokens on :root", "none");
    for (const n of names) {
      const v = tryResolve(n, reduced, LOADER);
      if (v.error || canon(v.value) !== "0ms") pass = report(`${id} ${n}`, "0ms under prefers-reduced-motion: reduce", v.error || v.value);
    }
    return pass;
  }
  let name = ticks(c0)[0];
  if (!name && /\(none\)/.test(c0)) {
    const arrow = (String(maps).match(/->\s*`(--[\w-]+)`/) || [])[1];
    if (arrow) name = arrow;
    else {
      /* "(none) | OV motion.duration.exit / easing.exit | 150ms / (0.3,0,1,1)": each part is an overlay token. */
      const paths = ovPaths(maps), vals = newc.split(" / ");
      if (!paths.length || paths.length !== vals.length || paths.some((p) => p.startsWith("?"))) return report(id, "OV paths matching the New values", `${maps} | ${newc}`);
      let pass = true;
      paths.forEach((p, k) => {
        const cls = newClass(vals[k].trim(), "", "");
        const exp = dsValue(p);
        if (!cls || canon(cls.value) !== canon(exp)) pass = report(`${id} ${p}`, `MAPPING ${vals[k]} = overlay ${exp}`, "mismatch");
        if (!ovResult.get(p)) pass = report(`${id} ${p}`, `overlay token declared as ${ovCandidates(p).join(" ")}`, "overlay check failed");
      });
      return pass;
    }
  }
  if (!name) return report(id, "a custom-property name in the first cell", bare(c0));
  const cls = newClass(newc, now, maps);
  if (!cls) return report(id, "a classifiable New cell", newc);
  const got = res(name);
  if (got.error) return report(`${id} ${name}`, cls.kind === "composite" ? "declared, every inner var() resolving" : `declared = ${newc}`, got.error);
  let oldValue;
  if (cls.kind === "keep") {
    const o = resOld(name);
    if (o.error) return report(`${id} ${name}`, `a ${BASE_REF} value`, o.error);
    oldValue = o.value;
  }
  let pass = judge(`${id} ${name}`, cls, got.value, oldValue);
  if (cls.note) {
    const d = dsCite(maps);
    if (d) { const dv = dsValue(d); if (canon(dv) !== canon(cls.value)) pass = report(`${id} ${name}`, `leading colour = DS ${d} ${dv}`, cls.value); }
  }
  return pass;
}

function emeraldRow(r, oldEm, newEm) {
  const [c0, val, key] = r.cells;
  const id = `MAPPING.md:${r.line}`;
  const name = ticks(c0)[0] || ticks(key)[0];
  if (!name) return report(id, "a --brand-* name", bare(c0));
  if (!newEm.has(name)) return report(`${id} ${name}`, `declared in [data-brand="emerald"]`, "absent");
  const scope = scopeMap(R, SCOPE.emerald);
  const rr = tryResolve(name, scope, LOADER);
  if (rr.error) return report(`${id} ${name}`, "resolves inside [data-brand=emerald]", rr.error);
  if (oldEm.has(name)) return canon(newEm.get(name)) === canon(oldEm.get(name)) ? true : report(`${id} ${name}`, `unchanged ${oldEm.get(name)}`, newEm.get(name));
  const v = bare(val).replace(/\s*\(.*\)$/, "");
  return canon(rr.value) === canon(v) ? true : report(`${id} ${name}`, v, rr.value);
}

const VIP_NAMES = [];
for (const t of tables) if (t.sec === 3 && t.header[0] === "Current" && t.header[1] === "New key") for (const r of t.rows) VIP_NAMES.push(ticks(r.cells[0])[0], ticks(r.cells[2])[0]);
function vipBlock(text) {
  const lines = text.split("\n");
  const idx = VIP_NAMES.map((n) => lines.findIndex((l) => new RegExp(`^\\s*${n}\\s*:`).test(l)));
  if (idx.some((k) => k < 0)) return null;
  return lines.slice(Math.min(...idx), Math.max(...idx) + 1).join("\n");
}
const vipOld = vipBlock(baseFile("src/styles/tokens.css"));
const vipNew = vipBlock(readFileSync(path.join(TARGET, "src/styles/tokens.css"), "utf8"));
const vipSame = vipOld !== null && vipOld === vipNew;
function vipRow(r) {
  const id = `MAPPING.md:${r.line}`;
  if (!vipSame) return report(id, `tokens.css VIP block byte-equal to ${BASE_REF}`, vipNew === null ? "a VIP name is missing" : "differs");
  let pass = true;
  for (const n of [ticks(r.cells[0])[0], ticks(r.cells[2])[0]]) {
    const a = res(n), b = resOld(n);
    if (a.error || b.error || canon(a.value) !== canon(b.value)) pass = report(`${id} ${n}`, b.value ?? b.error, a.value ?? a.error);
  }
  return pass;
}

function roleRow(r) {
  const [role, fam, size, lead, wt] = r.cells.map(bare);
  const id = `MAPPING.md:${r.line} role ${role}`;
  let pass = true;
  const base = `semantic.type.role.${role}`;
  const checks = [
    ["family", (v) => firstFamily(v) === fam.split(",")[0].trim().toLowerCase(), fam],
    ["size", (v) => { const mm = size.match(/^(\d+)-(\d+)px$/); if (!mm) return canon(v) === canon(size); const c = canon(v).match(/^clamp\((\d+)px,.*,(\d+)px\)$/); return !!c && c[1] === mm[1] && c[2] === mm[2]; }, size],
    ["leading", (v) => canon(v) === canon(lead), lead],
    ["weight", (v) => canon(v) === canon(wt), wt],
  ];
  for (const [prop, test, cell] of checks) {
    const p = `${base}.${prop}`;
    let v;
    try { v = dsValue(p); } catch (e) { pass = report(id, `overlay ${p}`, e.message); continue; }
    if (!test(v)) pass = report(`${id} ${prop}`, `MAPPING ${cell} = overlay ${v}`, "mismatch");
    if (!ovResult.get(p)) pass = report(`${id} ${prop}`, `overlay ${p} declared as ${ovCandidates(p).join(" ")}`, "overlay check failed");
  }
  return pass;
}

function breakpointRow(r) {
  const id = `MAPPING.md:${r.line}`;
  const widths = [...bare(r.cells[0]).matchAll(/\b(\d{3,4})\b/g)].map((m) => m[1]);
  if (!widths.length) return report(id, "breakpoint widths", bare(r.cells[0]));
  let pass = true;
  for (const w of widths) {
    const re = new RegExp(`\\b(min|max)-width:\\s*${w}px|width\\s*[<>]=?\\s*${w}px`);
    if (![...mediaPreludes].some((c) => /^@media/.test(c) && re.test(c))) pass = report(`${id} ${w}px`, `an @media query at ${w}px in the built CSS`, "absent");
  }
  return pass;
}

/* ---------------------------------------------------------------- run every row */

const oldEm = scopeMap(baseRules, ["[data-brand=emerald]"]);
const newEm = scopeMap(R, ["[data-brand=emerald]"]);
const perSec = new Map();
let rows = 0, rowsOk = 0;
for (const t of tables) {
  const h = t.header.join("|");
  for (const r of t.rows) {
    let pass;
    if (genericTables.includes(t)) pass = genericRow(r);
    else if (t.sec === 3 && h.startsWith("Current|Value (unchanged)|New key")) pass = emeraldRow(r, oldEm, newEm);
    else if (t.sec === 3 && h === "Current|New key|Current|New key") pass = vipRow(r);
    else if (t.sec === 4 && h.startsWith("Role|Family|Size|Leading|Weight")) pass = roleRow(r);
    else if (t.sec === 10 && h.startsWith("Width|")) pass = breakpointRow(r);
    else pass = report(`MAPPING.md:${r.line}`, "a row of a known table class", h);
    const s = perSec.get(t.sec) || { n: 0, ok: 0 };
    s.n++; if (pass) s.ok++;
    perSec.set(t.sec, s);
    rows++; if (pass) rowsOk++;
  }
}
for (const [sec, s] of [...perSec].sort((a, b) => a[0] - b[0])) console.log(`§${sec} ${s.ok === s.n ? "OK" : "FAILED"} ${s.ok}/${s.n}`);
const ovOk = [...ovResult.values()].filter(Boolean).length;
console.log(`OVERLAY ${ovOk === ov.size ? "OK" : "FAILED"} ${ovOk}/${ov.size}`);

/* ---------------------------------------------------------------- obsidian (MAPPING.md:158, D-DS4, D-DS8) */

let obsOk = 0, obsN = 0;
{
  const k = MD.findIndex((l) => l.startsWith('`[data-theme="obsidian"]`'));
  const text = k >= 0 ? MD[k] : "";
  const pairs = [...text.matchAll(/`(--[\w-]+)` (#[0-9a-fA-F]{3,8}|rgba\([^)]*\))/g)].map((m) => [m[1], m[2]]);
  const OBS = scopeMap(R, SCOPE.obsidian);
  const oldRoot = scopeMap(parseCss(baseFile("src/styles/tokens.css")), [":root"]);
  const legacy = new Set(["--money-positive", "--money-negative", "--status-danger-fg", "--state-focus-ring"]);
  for (const [sem, val] of pairs) {
    obsN++;
    const id = `obsidian MAPPING.md:${k + 1} ${sem}`;
    const cur = semIndex.get(sem);
    if (!cur) { report(id, "a current name through the §2 Maps-to column", "none"); continue; }
    const r = tryResolve(cur, OBS, LOADER);
    if (r.error) { report(`${id} ${cur}`, val, r.error); continue; }
    let pass = canon(r.value) === canon(val) || report(`${id} ${cur}`, val, r.value);
    if (legacy.has(sem)) {
      const o = oldRoot.get(cur);
      if (!o || canon(o) !== canon(r.value)) pass = report(`${id} ${cur}`, `${BASE_REF} tokens.css literal ${o ?? "none"}`, r.value);
    }
    if (pass) obsOk++;
  }
  if (obsN === 20 && obsOk === 20) console.log("OBSIDIAN OK 20/20");
  else { report("obsidian", "20 names (16 ladder + 4 legacy) all resolving", `${obsOk}/${obsN}`); console.log(`OBSIDIAN FAILED ${obsOk}/${obsN}`); }
}

/* ---------------------------------------------------------------- --wg-color-* = JSON $value */

let wgN = 0, wgOk = 0;
{
  const index = new Map();
  for (const p of tokens().all.keys()) if (p.startsWith("primitive.color.")) index.set(wgColourName(p), p);
  for (const r of R) for (const d of r.decls) {
    if (!d.p.startsWith("--wg-color-")) continue;
    wgN++;
    const p = index.get(d.p);
    if (!p) { report(`wg ${d.p}`, "a primitive.color token in design-tokens.all.json or the overlay", "none"); continue; }
    const v = dsValue(p);
    colourOf(d.v) && canon(d.v) === canon(v) ? wgOk++ : report(`wg ${d.p}`, `${p} ${v}`, d.v);
  }
  console.log(`WG-COLOR ${wgOk === wgN ? "OK" : "FAILED"} ${wgOk}/${wgN}`);
}

const N = rows + ov.size;
const good = rowsOk + ovOk;
const all = good === N && obsN === 20 && obsOk === 20 && wgOk === wgN;
console.log(all ? `PARITY OK ${N}/${N}` : `PARITY FAILED ${good}/${N}`);
process.exit(all ? 0 : 1);
