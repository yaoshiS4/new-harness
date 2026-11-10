#!/usr/bin/env node
/* rebuild-rules: token-anchored rule gate for the Tailwind translation.
 *
 * Usage:  node scripts/rebuild-rules.mjs <file|dir|dir/**|glob> ...
 *         node scripts/rebuild-rules.mjs --self-test
 *
 * Prints one `path:line: <rule-id> <token>` line per hit, then `RULES OK n files`.
 * Any hit, unknown flag, or argument matching no file exits 1. */

import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { expandArgs, extractClassTokens, extractComments, splitToken, lineAt, blankComments } from "./class-tokens.mjs";

const CLASS_RULES = [
  ["R-bp", "variant", /(^|:)(max-)?(sm|md|lg|xl|2xl):/],
  ["R-max-arb", "variant", /(^|:)max-\[/],
  ["R-transform", "utility", /^-?(scale|rotate|translate|skew)(-|$)/],
  ["R-bg-var", "utility", /^bg-\(--/],
  ["R-gradient", "utility", /^(bg-(linear|radial|conic)-|from-|via-|to-)/],
  ["R-opacity", "utility", /^(bg|text|border|fill|stroke|outline|decoration|accent|caret|placeholder|divide|ring|shadow)-[^/[]+\/[0-9]+$/],
  ["R-depth", "utility", /^(shadow|ring|inset-shadow|inset-ring|drop-shadow|backdrop-blur)(-|$)/],
  ["R-radius", "utility", /^rounded-full$/],
  ["R-transition", "utility", /^transition(-(all|colors|opacity|shadow|transform))?$|^(duration|delay)-[0-9]|^ease-(in|out|in-out|linear)$/],
  ["R-divide", "utility", /^divide-/],
  ["R-grid", "utility", /^grid-(cols|rows)-[0-9]+$/],
];

const SOURCE_RULES = [
  ["R-tw-merge", /tailwind-merge/],
  ["R-module-css", /\.module\.css/],
];

const TAG_RE =
  /\b(SPEC|GC|BR|UT|ST|FR|DEFECT|CASE|UC|NFR|AC|OD|SH|UIM|FC|REWARDS|ADR|RG)-[0-9]+\b|\bJ[0-9]+\b|\bWave [0-9]|\bruling [A-Z][0-9]+\b|\bPR-[0-9]{2}\b|\bleaf-[A-Z][0-9]/g;
const TERM_RE = /decree|nghị định|giấy phép|statute|regulat|licen[cs]|complian|pháp luật|thông tư/giu;

const CSS_AT_RE = /@(utility|apply|custom-variant|theme|layer|import)\b/g;
const KEYFRAMES_RE = /@keyframes\s+([^\s{]+)/g;

const isPartial = (rel) => /(^|\/)src\/styles\/areas\/[^/]+\.css$/.test(rel);
const isUiCss = (rel) => /(^|\/)src\/ui\/ui\.css$/.test(rel);

function loadAllow(root) {
  const f = path.join(root, "scripts", "rebuild-rules.allow.json");
  const set = new Set();
  if (!existsSync(f)) return set;
  const data = JSON.parse(readFileSync(f, "utf8"));
  if (Array.isArray(data)) for (const k of data) set.add(String(k));
  else for (const [file, lines] of Object.entries(data)) for (const l of lines) set.add(`${file}:${l}`);
  return set;
}

function lintFile(rel, text, allow) {
  const hits = [];
  const add = (line, id, token) => hits.push(`${rel}:${line}: ${id} ${token}`);
  const isScript = rel.endsWith(".ts") || rel.endsWith(".tsx");
  const isCss = rel.endsWith(".css");

  if (isScript) {
    for (const { token, line } of extractClassTokens(text)) {
      const { variant, utility, important } = splitToken(token);
      for (const [id, part, re] of CLASS_RULES) {
        if (re.test(part === "variant" ? variant : utility)) add(line, id, token);
      }
      if ((important || token.startsWith("!") || token.endsWith("!")) && !allow.has(`${rel}:${line}`)) {
        add(line, "R-important", token);
      }
    }
  }

  const code = blankComments(text, isScript);
  for (const [id, re] of SOURCE_RULES) {
    const g = new RegExp(re.source, "g");
    let m;
    while ((m = g.exec(code))) add(lineAt(text, m.index), id, m[0]);
  }

  if (isCss) {
    if (isPartial(rel) || isUiCss(rel)) {
      CSS_AT_RE.lastIndex = 0;
      let m;
      while ((m = CSS_AT_RE.exec(code))) add(lineAt(text, m.index), "R-css-at", m[0]);
    }
    if (isUiCss(rel)) {
      KEYFRAMES_RE.lastIndex = 0;
      let m;
      while ((m = KEYFRAMES_RE.exec(code))) add(lineAt(text, m.index), "R-kf-ui", m[1]);
    }
  }

  for (const c of extractComments(text, isScript)) {
    const lines = c.text.split("\n");
    lines.forEach((ln, k) => {
      for (const m of ln.matchAll(TAG_RE)) add(c.line + k, "R-comment-tag", m[0]);
      for (const m of ln.matchAll(TERM_RE)) add(c.line + k, "R-comment-term", m[0]);
    });
  }
  return hits;
}

/* @keyframes names must be unique across every .css file under <root>/src plus the arguments. */
function keyframeDupes(root, cssFiles) {
  const all = new Set(cssFiles);
  const srcDir = path.join(root, "src");
  if (existsSync(srcDir)) for (const f of expandArgs(["src"], root, [".css"]).files) all.add(f);
  const seen = new Map();
  for (const rel of [...all].sort()) {
    const text = readFileSync(path.resolve(root, rel), "utf8");
    const code = blankComments(text, false);
    KEYFRAMES_RE.lastIndex = 0;
    let m;
    while ((m = KEYFRAMES_RE.exec(code))) {
      const at = `${rel}:${lineAt(text, m.index)}`;
      if (!seen.has(m[1])) seen.set(m[1], []);
      seen.get(m[1]).push(at);
    }
  }
  const hits = [];
  for (const [name, where] of seen) {
    if (where.length > 1) for (const at of where.slice(1)) hits.push(`${at}: R-kf-dup ${name} (first at ${where[0]})`);
  }
  return hits;
}

export function run(args, root) {
  const { files, errors } = expandArgs(args, root, [".ts", ".tsx", ".css"]);
  if (errors.length) return { code: 1, lines: errors.map((e) => `rebuild-rules: ${e}`) };
  const allow = loadAllow(root);
  const hits = [];
  for (const rel of files) hits.push(...lintFile(rel, readFileSync(path.resolve(root, rel), "utf8"), allow));
  hits.push(...keyframeDupes(root, files.filter((f) => f.endsWith(".css"))));
  if (hits.length) return { code: 1, lines: [...hits, `RULES FAILED ${hits.length} hits in ${files.length} files`] };
  return { code: 0, lines: [`RULES OK ${files.length} files`] };
}

function selfTest() {
  const tmp = mkdtempSync(path.join(tmpdir(), "rebuild-rules-"));
  let n = 0;
  /* Each seed gets its own root, so the tree-wide keyframe scan sees only that seed. */
  const put = (rel, text, extra = {}) => {
    const root = path.join(tmp, `seed-${n++}`);
    for (const [r, t] of Object.entries({ [rel]: text, ...extra })) {
      mkdirSync(path.dirname(path.join(root, r)), { recursive: true });
      writeFileSync(path.join(root, r), t);
    }
    return { rel, root };
  };
  const tsx = (cls) => `export const X = () => <div className="${cls}" />;\n`;
  const positives = [
    ["R-bp", put("src/p/bp.tsx", tsx("md:p-space-2"))],
    ["R-max-arb", put("src/p/max-arb.tsx", tsx("max-[639px]:p-space-2"))],
    ["R-transform", put("src/p/transform.tsx", tsx("scale-105"))],
    ["R-bg-var", put("src/p/bg-var.tsx", tsx("bg-(--brand-accent)"))],
    ["R-gradient", put("src/p/gradient.tsx", tsx("bg-linear-to-r"))],
    ["R-opacity", put("src/p/opacity.tsx", tsx("bg-canvas/50"))],
    ["R-depth", put("src/p/depth.tsx", tsx("shadow-md"))],
    ["R-radius", put("src/p/radius.tsx", tsx("rounded-full"))],
    ["R-transition", put("src/p/transition.tsx", tsx("transition-colors"))],
    ["R-divide", put("src/p/divide.tsx", tsx("divide-y"))],
    ["R-grid", put("src/p/grid.tsx", tsx("grid-cols-3"))],
    ["R-important", put("src/p/important.tsx", tsx("p-space-2!"))],
    ["R-tw-merge", put("src/p/twmerge.ts", `import { twMerge } from "tailwind-merge";\nexport const m = twMerge;\n`)],
    ["R-module-css", put("src/p/module.tsx", `import s from "./X.module.css";\nexport const c = s;\n`)],
    ["R-css-at", put("src/styles/areas/vip.css", `@utility x {}\n`)],
    ["R-kf-ui", put("src/ui/ui.css", `@keyframes ui-own { from { opacity: 0; } }\n`)],
    ["R-kf-dup", put("src/styles/areas/lottery.css", `@keyframes bob { from { opacity: 0; } }\n@keyframes bob { to { opacity: 1; } }\n`)],
    ["R-comment-tag", put("src/p/wave.tsx", `// Wave 3 hero\nexport const a = 1;\n`)],
    ["R-comment-tag", put("src/p/j.ts", `/* counted in J9 */\nexport const b = 1;\n`)],
    ["R-comment-tag", put("src/p/spec.css", `/* SPEC-02 token split */\n.a { color: red; }\n`)],
    ["R-comment-term", put("src/p/decree.tsx", `{/* Decree-174 */}\nexport const d = 1;\n`)],
  ];
  const tokenLines = [
    "--t-sm:      14px;",
    "--t-num-lg:  32px; /* hero tabular money */",
    "--radius-sm:   4px;",
    "--radius-md:   8px;",
    "--radius-lg:   12px;",
    "--shadow-2:  none;",
    "--gap-sm:      8px;    /* dense tile clusters, chip rows (×35) */",
    "--card-pad-sm: 16px;   /* standard card padding (×16) */",
  ];
  const cleanTokens = [
    "[transform:translate(-50%,-50%)]",
    "[transform:scale(1.02)]",
    "aspect-[16/9]",
    "top-1/2",
    "max-639:p-space-2",
    "min-[768px]:p-space-2",
    "grid-cols-[repeat(3,1fr)]",
    "duration-(--dur-fast)",
    "hover-fine:bg-surface",
    "[@media(hover:hover)]:hover:bg-surface",
    "cycle",
    "stateLabel",
  ];
  const cleans = [
    ...tokenLines.map((l, k) => [l, put(`src/c/tokens-${k}/tokens.css`, `:root {\n  ${l}\n}\n`)]),
    ["transition: in css", put("src/styles/areas/home.css", `.tile {\n  transition: transform var(--dur-fast) var(--ease-standard);\n}\n`)],
    ...cleanTokens.map((t, k) => [t, put(`src/c/class-${k}.tsx`, tsx(t))]),
    ["rendered YB-668812", put("src/c/rendered.tsx", `export const M = () => <span className="text-text-mid">YB-668812</span>;\n`)],
    ["dir [vertical]", { ...put("src/app/[vertical]/page.tsx", tsx("p-space-2")), rel: "src/app/[vertical]" }],
  ];

  let ok = 0;
  const total = positives.length + cleans.length;
  for (const [id, { rel, root }] of positives) {
    const r = run([rel], root);
    const fired = r.code === 1 && r.lines.some((l) => l.split(" ")[1] === id);
    if (fired) ok++;
    console.log(`  seed + ${id} ${rel}: ${fired ? "fires" : "DID NOT FIRE"} (${r.lines[0]})`);
  }
  for (const [label, { rel, root }] of cleans) {
    const r = run([rel], root);
    const clean = r.code === 0 && r.lines[r.lines.length - 1].startsWith("RULES OK ") && !r.lines[0].startsWith("RULES OK 0 ");
    if (clean) ok++;
    console.log(`  seed - ${label}: ${clean ? "clean" : "UNEXPECTED: " + r.lines.join(" | ")}`);
  }
  const empty = run(["src/does-not-exist/**"], put("src/a.tsx", tsx("p-space-2")).root);
  const emptyOk = empty.code === 1;
  console.log(`  seed + no-match argument: ${emptyOk ? "exits 1" : "DID NOT FAIL"}`);
  rmSync(tmp, { recursive: true, force: true });
  if (ok === total && emptyOk) {
    console.log(`SELF-TEST OK: ${positives.length} positive seeds fire, ${cleans.length} clean seeds pass.`);
    return 0;
  }
  console.log(`SELF-TEST FAILED: ${ok}/${total} seeds behaved`);
  return 1;
}

const argv = process.argv.slice(2);
const unknown = argv.filter((a) => a.startsWith("--") && a !== "--self-test");
if (unknown.length) {
  console.error(`rebuild-rules: unknown flag ${unknown[0]}`);
  process.exit(1);
}
if (argv.includes("--self-test")) process.exit(selfTest());
if (argv.length === 0) {
  console.error("rebuild-rules: no file arguments");
  process.exit(1);
}
const r = run(argv, process.cwd());
for (const l of r.lines) (r.code ? console.error : console.log)(l);
process.exit(r.code);
