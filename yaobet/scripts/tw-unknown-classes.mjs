#!/usr/bin/env node
/* tw-unknown-classes: flags className tokens that compile to no CSS.
 *
 * Each unique class token is compiled with the installed `tailwindcss`
 * compile() against the repo's real src/app/globals.css. A token whose CSS is
 * empty is reported unless it is a class declared in src/ui/ui.css or
 * src/styles/**\/*.css, or one of the fixed hooks below.
 *
 * Usage:  node scripts/tw-unknown-classes.mjs <file|dir|dir/**|glob> ...
 *         node scripts/tw-unknown-classes.mjs --emit <token>
 *         node scripts/tw-unknown-classes.mjs --self-test */

import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import path from "node:path";
import { compile } from "tailwindcss";
import { expandArgs, extractClassTokens } from "./class-tokens.mjs";

const require = createRequire(import.meta.url);
const FIXED = [/^group(\/[\w-]+)?$/, /^peer(\/[\w-]+)?$/, /^cycle$/, /^stateLabel$/, /^active$/];

async function loadStylesheet(id, base) {
  const file = id.startsWith(".") || path.isAbsolute(id) ? path.resolve(base, id) : require.resolve(id, { paths: [base] });
  return { path: file, base: path.dirname(file), content: readFileSync(file, "utf8") };
}

async function makeCompiler(entry) {
  const css = readFileSync(entry, "utf8");
  return compile(css, { base: path.dirname(entry), from: entry, loadStylesheet });
}

/* Class selectors declared in a stylesheet (selector preludes only, never values). */
function declaredClasses(css) {
  const out = new Set();
  const text = css.replace(/\/\*[\s\S]*?\*\//g, "").replace(/"[^"]*"|'[^']*'/g, '""');
  const re = /([^{};]*)\{/g;
  let m;
  while ((m = re.exec(text))) {
    const prelude = m[1].trim();
    if (prelude.startsWith("@")) continue;
    for (const c of prelude.matchAll(/\.(-?[_a-zA-Z][_a-zA-Z0-9-]*)/g)) out.add(c[1]);
  }
  return out;
}

function allowList(root) {
  const allow = new Set();
  const { files } = expandArgs(["src/ui/ui.css", "src/styles"], root, [".css"]);
  for (const rel of files) for (const c of declaredClasses(readFileSync(path.resolve(root, rel), "utf8"))) allow.add(c);
  return allow;
}

/* The CSS one token adds on top of the base build (the utilities block). */
async function emitFor(entry, token) {
  const compiler = await makeCompiler(entry);
  const base = compiler.build([]);
  const out = compiler.build([token]);
  if (out === base) return "";
  let i = 0;
  while (i < base.length && base[i] === out[i]) i++;
  let j = 0;
  while (j < base.length - i && base[base.length - 1 - j] === out[out.length - 1 - j]) j++;
  return out.slice(i, out.length - j);
}

export async function run(args, root) {
  const { files, errors } = expandArgs(args, root, [".ts", ".tsx"]);
  if (errors.length) return { code: 1, lines: errors.map((e) => `tw-unknown-classes: ${e}`) };
  const entry = path.join(root, "src", "app", "globals.css");
  if (!existsSync(entry)) return { code: 1, lines: [`tw-unknown-classes: ${path.relative(root, entry)} missing`] };
  const uses = new Map();
  for (const rel of files) {
    for (const { token, line } of extractClassTokens(readFileSync(path.resolve(root, rel), "utf8"))) {
      if (!uses.has(token)) uses.set(token, []);
      uses.get(token).push(`${rel}:${line}`);
    }
  }
  const allow = allowList(root);
  const compiler = await makeCompiler(entry);
  let prev = compiler.build([]);
  const hits = [];
  for (const [token, where] of [...uses].sort((a, b) => a[0].localeCompare(b[0]))) {
    const out = compiler.build([token]);
    const empty = out === prev;
    prev = out;
    if (!empty || allow.has(token) || FIXED.some((re) => re.test(token))) continue;
    for (const at of where) hits.push(`${at}: unknown-class ${token}`);
  }
  if (hits.length) return { code: 1, lines: [...hits, `CLASSES FAILED ${hits.length} hits, ${uses.size} tokens`] };
  return { code: 0, lines: [`CLASSES OK ${uses.size} tokens`] };
}

async function selfTest() {
  const tmp = mkdtempSync(path.join(tmpdir(), "tw-unknown-"));
  const put = (rel, text) => {
    mkdirSync(path.dirname(path.join(tmp, rel)), { recursive: true });
    writeFileSync(path.join(tmp, rel), text);
  };
  const twDir = path.dirname(require.resolve("tailwindcss/package.json"));
  put(
    "src/app/globals.css",
    [
      "@layer theme, base, components, utilities;",
      `@import "${path.join(twDir, "theme.css")}" layer(theme);`,
      `@import "${path.join(twDir, "utilities.css")}" layer(utilities) source(none);`,
      '@import "../styles/tw-theme.css";',
      '@source "../";',
      "@custom-variant hover (&:hover);",
      '@import "../ui/ui.css" layer(components);',
      "",
    ].join("\n"),
  );
  put("src/styles/tw-theme.css", "@theme inline reference {\n  --*: initial;\n  --color-surface: var(--surface);\n}\n");
  put("src/ui/ui.css", ".ui-btn {\n  display: inline-flex;\n}\n");
  const flagged = ["p-4", "text-sm", "h-9", "hover-any:x"];
  const clean = ["cycle", "stateLabel", "ui-btn", "group", "active", "bg-surface"];
  put("src/x/Seed.tsx", `export const S = () => <div className="${[...flagged, ...clean].join(" ")}" />;\n`);
  const r = await run(["src/x/Seed.tsx"], tmp);
  const got = new Set(r.lines.filter((l) => l.includes(": unknown-class ")).map((l) => l.split(" ").pop()));
  let ok = 0;
  for (const t of flagged) {
    const pass = got.has(t);
    if (pass) ok++;
    console.log(`seed + ${t}: ${pass ? "flagged" : "NOT FLAGGED"}`);
  }
  for (const t of clean) {
    const pass = !got.has(t);
    if (pass) ok++;
    console.log(`seed - ${t}: ${pass ? "clean" : "FLAGGED"}`);
  }
  const emitted = await emitFor(path.join(tmp, "src/app/globals.css"), "hover:bg-surface");
  const emitOk = emitted.includes(":hover") && !emitted.includes("@media");
  console.log(`seed --emit hover:bg-surface: ${emitOk ? "plain :hover" : "UNEXPECTED " + JSON.stringify(emitted)}`);
  rmSync(tmp, { recursive: true, force: true });
  const total = flagged.length + clean.length;
  if (ok === total && emitOk && r.code === 1) {
    console.log(`SELF-TEST OK: ${flagged.length} stock or unknown tokens flagged, ${clean.length} declared tokens clean.`);
    return 0;
  }
  console.log(`SELF-TEST FAILED: ${ok}/${total} seeds behaved`);
  return 1;
}

const argv = process.argv.slice(2);
const KNOWN = new Set(["--self-test", "--emit"]);
const bad = argv.find((a) => a.startsWith("--") && !KNOWN.has(a));
if (bad) {
  console.error(`tw-unknown-classes: unknown flag ${bad}`);
  process.exit(1);
}
if (argv.includes("--self-test")) process.exit(await selfTest());
if (argv[0] === "--emit") {
  if (argv.length !== 2) {
    console.error("tw-unknown-classes: --emit takes exactly one token");
    process.exit(1);
  }
  const entry = path.join(process.cwd(), "src", "app", "globals.css");
  if (!existsSync(entry)) {
    console.error("tw-unknown-classes: src/app/globals.css missing");
    process.exit(1);
  }
  process.stdout.write((await emitFor(entry, argv[1])) + "\n");
  process.exit(0);
}
if (argv.length === 0 || argv.includes("--emit")) {
  console.error("tw-unknown-classes: no file arguments");
  process.exit(1);
}
const r = await run(argv, process.cwd());
for (const l of r.lines) (r.code ? console.error : console.log)(l);
process.exit(r.code);
