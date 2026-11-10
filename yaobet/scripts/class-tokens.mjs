/* Shared helpers for the rule gates (rebuild-rules.mjs, tw-unknown-classes.mjs).
 * Zero dependencies: argument expansion, class-token extraction from .ts/.tsx,
 * comment extraction, and the variant / utility split of a class token. */

import { existsSync, readdirSync, statSync } from "node:fs";
import path from "node:path";

const SKIP_DIRS = new Set(["node_modules", ".next", ".git"]);

function walk(dir, out = []) {
  for (const entry of readdirSync(dir)) {
    if (SKIP_DIRS.has(entry)) continue;
    const p = path.join(dir, entry);
    if (statSync(p).isDirectory()) walk(p, out);
    else out.push(p);
  }
  return out;
}

/** Expand `{a,b}` groups (nested allowed); `[` and `]` stay literal. */
export function expandBraces(arg) {
  const open = arg.indexOf("{");
  if (open === -1) return [arg];
  let depth = 0;
  let close = -1;
  const commas = [];
  for (let i = open; i < arg.length; i++) {
    if (arg[i] === "{") depth++;
    else if (arg[i] === "}") {
      depth--;
      if (depth === 0) {
        close = i;
        break;
      }
    } else if (arg[i] === "," && depth === 1) commas.push(i);
  }
  if (close === -1 || commas.length === 0) return [arg];
  const head = arg.slice(0, open);
  const tail = arg.slice(close + 1);
  const parts = [];
  let start = open + 1;
  for (const c of [...commas, close]) {
    parts.push(arg.slice(start, c));
    start = c + 1;
  }
  return parts.flatMap((p) => expandBraces(head + p + tail));
}

function globToRegExp(glob) {
  let re = "";
  for (let i = 0; i < glob.length; i++) {
    const ch = glob[i];
    if (ch === "*") {
      if (glob[i + 1] === "*") {
        i++;
        if (glob[i + 1] === "/") {
          i++;
          re += "(?:.*/)?";
        } else re += ".*";
      } else re += "[^/]*";
    } else if ("\\^$.|?+()[]{}".includes(ch)) re += "\\" + ch;
    else re += ch;
  }
  return new RegExp("^" + re + "$");
}

/**
 * Expand file, directory and glob arguments (`dir/**`, `*.css`, braces).
 * Returns { files, errors }: an argument that matches no file is an error.
 * Paths are returned relative to `root`, with forward slashes.
 */
export function expandArgs(args, root, exts) {
  const files = new Set();
  /* Inside the root: a root-relative path; outside it: the absolute path. */
  const relOf = (f) => {
    const rel = path.relative(root, f);
    return rel.startsWith("..") ? f : rel.split(path.sep).join("/");
  };
  const errors = [];
  const keep = (rel) => exts.some((e) => rel.endsWith(e));
  for (const raw of args) {
    let matched = 0;
    for (const arg of expandBraces(raw)) {
      const norm = arg.replace(/\\/g, "/").replace(/\/+$/, "");
      if (!norm.includes("*")) {
        const abs = path.resolve(root, norm);
        if (!existsSync(abs)) continue;
        const list = statSync(abs).isDirectory() ? walk(abs) : [abs];
        for (const f of list) {
          matched++;
          const rel = relOf(f);
          if (keep(rel)) files.add(rel);
        }
        continue;
      }
      const segs = norm.split("/");
      const fixed = [];
      for (const s of segs) {
        if (s.includes("*")) break;
        fixed.push(s);
      }
      const baseAbs = path.resolve(root, fixed.join("/") || ".");
      if (!existsSync(baseAbs) || !statSync(baseAbs).isDirectory()) continue;
      const re = globToRegExp(path.relative(root, path.resolve(root, norm)).split(path.sep).join("/"));
      for (const f of walk(baseAbs)) {
        const rel = path.relative(root, f).split(path.sep).join("/");
        if (!re.test(rel)) continue;
        matched++;
        if (keep(rel)) files.add(rel);
      }
    }
    if (matched === 0) errors.push(`argument matches no file: ${raw}`);
  }
  return { files: [...files].sort(), errors };
}

/** Line number (1-based) of offset `i` in `text`. */
export function lineAt(text, i) {
  let n = 1;
  for (let k = 0; k < i && k < text.length; k++) if (text.charCodeAt(k) === 10) n++;
  return n;
}

/**
 * Comments of a source file, as { text, line }. Block comments (`/* … *\/`,
 * which covers JSX `{/* … *\/}`) always; line comments (`// …`) for scripts
 * only, when the slashes follow start of line, whitespace or punctuation (so
 * `https://` inside a string is not a comment).
 */
export function extractComments(src, isScript) {
  const out = [];
  const re = isScript ? /\/\*[\s\S]*?\*\/|(^|[\s;,{}()])(\/\/[^\n]*)/g : /\/\*[\s\S]*?\*\//g;
  let m;
  while ((m = re.exec(src))) {
    if (m[2] !== undefined) {
      const at = m.index + m[1].length;
      out.push({ text: m[2], line: lineAt(src, at) });
    } else out.push({ text: m[0], line: lineAt(src, m.index) });
  }
  return out;
}

/** Same text with comments replaced by spaces (newlines kept), for trigger search. */
export function blankComments(src, isScript) {
  const re = isScript ? /\/\*[\s\S]*?\*\/|(^|[\s;,{}()])(\/\/[^\n]*)/g : /\/\*[\s\S]*?\*\//g;
  return src.replace(re, (all, pre, line) => {
    if (line !== undefined) return pre + " ".repeat(line.length);
    return all.replace(/[^\n]/g, " ");
  });
}

/* Read a quoted string starting at `i` (quote char at src[i]); returns end index after the closing quote. */
function readQuoted(src, i) {
  const q = src[i];
  let j = i + 1;
  while (j < src.length && src[j] !== q) {
    if (src[j] === "\\") j++;
    else if (src[j] === "\n") break;
    j++;
  }
  return j + 1;
}

const COMBINERS = new Set(["cn", "clsx", "cx"]);
const KEYWORDS = new Set(["return", "typeof", "await", "yield", "void", "case", "in", "of", "else", "delete", "instanceof"]);

/* True when the "(" at `i` opens a call whose callee (identifier or member chain) is not a class combiner. */
function isPlainCall(src, i) {
  let j = i - 1;
  while (j >= 0 && /\s/.test(src[j])) j--;
  let k = j;
  while (k >= 0 && /[\w$.]/.test(src[k])) k--;
  const callee = src.slice(k + 1, j + 1);
  if (!/^\.?[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*$/.test(callee)) return false;
  return !COMBINERS.has(callee) && !KEYWORDS.has(callee);
}

/* True when the literal spanning [start, end) is an operand of ==, !=, === or !== (either side). */
function isComparand(src, start, end) {
  let j = start - 1;
  while (j >= 0 && /\s/.test(src[j])) j--;
  if (src[j] === "=" && (src[j - 1] === "=" || src[j - 1] === "!")) return true;
  let k = end;
  while (k < src.length && /\s/.test(src[k])) k++;
  return (src[k] === "=" || src[k] === "!") && src[k + 1] === "=";
}

/*
 * Scan an expression from `i` until the bracket that closes it (depth < 0) or,
 * when `stopAtDepth0` is set, until the first top-level string literal ends.
 * Every string literal and template static part found is reported through
 * `emit(text, offset)`, except operands of ==, !=, ===, !==; template `${…}`
 * holes become the literal marker `${}` and their contents are scanned recursively.
 */
function scanExpr(src, i, emit, closer) {
  let depth = 0;
  while (i < src.length) {
    const ch = src[i];
    if (ch === "/" && src[i + 1] === "*") {
      const e = src.indexOf("*/", i + 2);
      i = e === -1 ? src.length : e + 2;
      continue;
    }
    if (ch === "/" && src[i + 1] === "/") {
      const e = src.indexOf("\n", i);
      i = e === -1 ? src.length : e;
      continue;
    }
    if (ch === '"' || ch === "'") {
      const end = readQuoted(src, i);
      if (!isComparand(src, i, end)) emit(src.slice(i + 1, end - 1), i + 1);
      i = end;
      continue;
    }
    if (ch === "`") {
      const parts = [];
      const end = scanTemplate(src, i, (t, o) => parts.push([t, o]));
      if (!isComparand(src, i, end)) for (const [t, o] of parts) emit(t, o);
      i = end;
      continue;
    }
    if (ch === "(" && isPlainCall(src, i)) {
      i = scanExpr(src, i + 1, () => {}, ")");
      continue;
    }
    if (ch === "(" || ch === "[" || ch === "{") depth++;
    else if (ch === ")" || ch === "]" || ch === "}") {
      depth--;
      if (depth < 0) return ch === closer ? i + 1 : i;
    }
    i++;
  }
  return i;
}

function scanTemplate(src, i, emit) {
  let j = i + 1;
  let text = "";
  const start = j;
  while (j < src.length && src[j] !== "`") {
    if (src[j] === "\\") {
      text += src[j] + (src[j + 1] ?? "");
      j += 2;
      continue;
    }
    if (src[j] === "$" && src[j + 1] === "{") {
      text += "${}";
      j = scanExpr(src, j + 2, emit, "}");
      continue;
    }
    text += src[j];
    j++;
  }
  emit(text, start);
  return j + 1;
}

const TRIGGER = /(?<![\w$.-])(?:className|class)\s*=\s*|(?<![\w$.])(?:cn|clsx|cx)\s*\(/g;

/**
 * Class tokens of a .ts/.tsx source: string literals and template static parts
 * inside `className=`, `class=`, `cn(`, `clsx(`, `cx(`; split on whitespace;
 * tokens containing `${` are skipped. Returns [{ token, line }].
 */
export function extractClassTokens(src) {
  const code = blankComments(src, true);
  const out = [];
  const emit = (text, offset) => {
    const re = /\S+/g;
    let m;
    while ((m = re.exec(text))) {
      if (m[0].includes("${")) continue;
      out.push({ token: m[0], line: lineAt(src, offset + m.index) });
    }
  };
  TRIGGER.lastIndex = 0;
  let m;
  while ((m = TRIGGER.exec(code))) {
    let i = m.index + m[0].length;
    if (m[0].endsWith("(")) {
      scanExpr(code, i, emit, ")");
      continue;
    }
    const ch = code[i];
    if (ch === '"' || ch === "'") emit(code.slice(i + 1, readQuoted(code, i) - 1), i + 1);
    else if (ch === "{") scanExpr(code, i + 1, emit, "}");
    else if (ch === "`") scanTemplate(code, i, emit);
  }
  return out;
}

/** Split a class token into { variant, utility, important }. */
export function splitToken(token) {
  let t = token;
  let important = false;
  let depth = 0;
  let cut = -1;
  for (let i = 0; i < t.length; i++) {
    const ch = t[i];
    if (ch === "[" || ch === "(") depth++;
    else if (ch === "]" || ch === ")") depth--;
    else if (ch === ":" && depth === 0) cut = i;
  }
  const variant = cut === -1 ? "" : t.slice(0, cut + 1);
  let utility = cut === -1 ? t : t.slice(cut + 1);
  if (utility.startsWith("!")) {
    important = true;
    utility = utility.slice(1);
  }
  if (utility.endsWith("!")) {
    important = true;
    utility = utility.slice(0, -1);
  }
  return { variant, utility, important };
}
