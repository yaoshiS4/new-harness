#!/usr/bin/env node
/* verify-routes: the route inventory (26 page files, 43 URLs) against a running server.
 *
 * Usage:  node scripts/verify-routes.mjs [--base <url>] [--only </a,/b>]
 *         node scripts/verify-routes.mjs --list
 *         node scripts/verify-routes.mjs --build-log <file> [--base <url>]
 *
 * --base defaults to $BASE (exported by scripts/with-dev-server.mjs).
 * Prints `ROUTES OK n/n` only when n >= 1 and every URL answers as listed. */

import { existsSync, readFileSync } from "node:fs";

const VERTICALS = ["casino", "slots", "sports", "fishing", "card", "lottery", "cockfight", "table", "arcade"];
const PAGES_200 = [
  "/tai-khoan", "/vi-tien", "/tin-nhan", "/gioi-thieu", "/dai-ly", "/cuoc-hop-le",
  "/vip", "/tier", "/cau-lac-bo", "/cua-hang", "/ve-so", "/bo-suu-tap", "/bo-suu-tap/cua-toi",
  "/ho-tro", "/tro-giup", "/tai-app", "/phong-cach", "/dev/collection-ports",
];
const REDIRECTS = [
  ["/bao-mat", "/tai-khoan"],
  ["/lich-su", "/tai-khoan"],
  ["/hoan-tra", "/khuyen-mai"],
  ["/game-han-che", "/cuoc-hop-le?tab=han-che"],
];

/* [url, status, redirect target or null, robots meta marker (optional), meta refresh target (optional)] */
export const INVENTORY = [
  ["/", 200, null],
  ...VERTICALS.map((v) => [`/${v}`, 200, null]),
  ["/khuyen-mai", 200, null],
  ...Array.from({ length: 8 }, (_, i) => [`/khuyen-mai/pr${i + 1}`, 200, null]),
  ...PAGES_200.map((p) => [p, 200, null]),
  ...REDIRECTS.map(([from, to]) => [from, 200, null, null, to]),
  ["/foo", 200, null, "noindex"],
  ["/khuyen-mai/pr9", 200, null, "noindex"],
];

/* The 26 route patterns of the page files, as `next build` prints them (route groups dropped). */
export const PATTERNS = [
  "/", "/[vertical]", "/khuyen-mai", "/khuyen-mai/[id]",
  ...PAGES_200,
  ...REDIRECTS.map(([from]) => from),
];

function parseArgs(argv) {
  const opts = { base: process.env.BASE ?? "", only: null, list: false, buildLog: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const value = () => {
      const v = argv[++i];
      if (v === undefined || v.startsWith("--")) throw new Error(`${a} needs a value`);
      return v;
    };
    if (a === "--base") opts.base = value();
    else if (a === "--only") opts.only = value().split(",").map((s) => s.trim()).filter(Boolean);
    else if (a === "--list") opts.list = true;
    else if (a === "--build-log") opts.buildLog = value();
    else throw new Error(`unknown argument ${a}`);
  }
  return opts;
}

function checkBuildLog(file) {
  if (!existsSync(file)) return [`build log ${file} not found`];
  const seen = new Set();
  for (const line of readFileSync(file, "utf8").split("\n")) {
    const m = line.match(/^[\s│├└┌┬─]*(?:[○●ƒλ◐◇]\s+)?(\/\S*)/u);
    if (m) seen.add(m[1]);
  }
  return PATTERNS.filter((p) => !seen.has(p)).map((p) => `route pattern ${p} absent from the build route table`);
}

async function probe(base, [url, status, target, marker, refresh]) {
  let res;
  try {
    res = await fetch(base + url, { redirect: "manual", signal: AbortSignal.timeout(180000) });
  } catch (e) {
    return `Fail: ${url} | Expected: ${status} | Got: no response (${e.cause?.code ?? e.message})`;
  }
  const body = marker || refresh ? await res.text().catch(() => "") : await res.arrayBuffer().catch(() => {});
  if (res.status !== status) return `Fail: ${url} | Expected: ${status} | Got: ${res.status}`;
  if (target) {
    const loc = res.headers.get("location") ?? "";
    let got = loc;
    try {
      const u = new URL(loc, base);
      got = u.pathname + u.search;
    } catch {}
    if (got !== target) return `Fail: ${url} | Expected: 307 -> ${target} | Got: 307 -> ${loc || "(none)"}`;
  }
  if (marker && !body.includes(`name="robots" content="${marker}"`))
    return `Fail: ${url} | Expected: body with ${marker} | Got: absent`;
  if (refresh && !body.includes(`http-equiv="refresh" content="1;url=${refresh}"`))
    return `Fail: ${url} | Expected: body with refresh to ${refresh} | Got: absent`;
  return null;
}

async function main() {
  let opts;
  try {
    opts = parseArgs(process.argv.slice(2));
  } catch (e) {
    console.error(`verify-routes: ${e.message}`);
    return 1;
  }
  if (opts.list) {
    for (const [url] of INVENTORY) console.log(url);
    return 0;
  }
  let selected = INVENTORY;
  if (opts.only) {
    const known = new Map(INVENTORY.map((r) => [r[0], r]));
    const outside = opts.only.filter((u) => !known.has(u));
    if (outside.length) {
      console.error(`verify-routes: not in inventory: ${outside.join(", ")}`);
      return 1;
    }
    selected = opts.only.map((u) => known.get(u));
  }
  if (opts.buildLog) {
    const missing = checkBuildLog(opts.buildLog);
    if (missing.length) {
      for (const m of missing) console.error(`Fail: ${m}`);
      console.error(`INVENTORY FAILED ${PATTERNS.length - missing.length}/${PATTERNS.length}`);
      return 1;
    }
    console.log(`INVENTORY OK ${PATTERNS.length}/${PATTERNS.length}`);
    if (!opts.base && !opts.only) return 0;
  }
  if (!opts.base) {
    console.error("verify-routes: no server: pass --base <url> or run under scripts/with-dev-server.mjs");
    return 1;
  }
  const base = opts.base.replace(/\/+$/, "");
  let pass = 0;
  for (const row of selected) {
    const err = await probe(base, row);
    if (err) console.error(err);
    else {
      pass++;
      console.log(`ok ${row[1]} ${row[0]}${row[2] ? " -> " + row[2] : ""}`);
    }
  }
  if (selected.length >= 1 && pass === selected.length) {
    console.log(`ROUTES OK ${pass}/${selected.length}`);
    return 0;
  }
  console.error(`ROUTES FAILED ${pass}/${selected.length}`);
  return 1;
}

process.exit(await main());
