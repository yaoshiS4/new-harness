#!/usr/bin/env python3
"""Mechanical harness tree validator for the Claude Code SOTA Harness (Harness² protocol).

Checks (all must pass):
  1. Byte budget: .claude/GLOBAL_CLAUDE.md <= 12,000 chars; always-on rules
     (GLOBAL_CLAUDE.md + CLAUDE.md + .claude/rules/**/*.md) each <= 24,000 bytes
     and <= 64,000 bytes in total.
  2. Skill coverage & reach: every .claude/skills/<name>/SKILL.md has a
     non-empty description, is referenced by GLOBAL_CLAUDE.md, harness_lib
     ROLE_SKILL_BUNDLES, an agent's `skills:` list, a command, or the skillbank
     INDEX; no two skill descriptions have lexical similarity >= 0.90.
  3. Template braces: no unescaped `{{` / `{%` in GLOBAL_CLAUDE.md outside fences.
  4. Hooks, agents, commands, settings: every hook command in
     .claude/settings.json resolves to an existing file that py_compiles; every
     .claude/hooks/*.py compiles; agents have valid frontmatter (name == file,
     description, model in {inherit, sonnet, opus, haiku, fable}); commands have
     a description; .claude/settings.json and .mcp.json are valid JSON.
  5. CP-2 Security Guardrail Integrity: pre_tool_use.py keeps the vendor
     scout-block, privacy block, Story Shard lease enforcement, in-memory
     ast.parse gate, destructive command guard, and PM zero-code-write gate;
     settings.json registers PreToolUse, PostToolUse, and Stop hooks.

Usage: python3 scripts/validate-claude-tree.py [--root DIR] [--max-chars 12000] [--json]
"""
from __future__ import annotations

import argparse
import json
import math
import os

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "when", "use", "using", "via", "or", "of", "to", "in",
    "on", "a", "an", "by", "is", "are", "as", "it", "its", "be", "at", "not", "no", "all", "any", "per", "after",
    "before", "skill", "skills", "agent", "agents", "code", "tool", "tools", "run", "runs", "mode", "task", "tasks",
}
REQUIRED_AGENTS = (
    "pm", "dev-be", "dev-fe", "debugger", "oracle-review", "hallucination-auditor", "test-runner", "frontend-qc",
    "backend-explorer", "frontend-explorer", "research-explorer", "sa", "critical-planner",
)


def tokens(text: str) -> list:
    return [t for t in re.findall(r"\b[a-z0-9_]{2,}\b", text.lower()) if t not in STOPWORDS]


def jaccard(a: list, b: list) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def bm25_cosine(docs: list) -> dict:
    """Pairwise BM25-weighted cosine similarity (k1=1.5, b=0.75)."""
    n = len(docs)
    if n < 2:
        return {}
    avgdl = sum(len(d) for d in docs) / n
    df = Counter()
    for d in docs:
        for t in set(d):
            df[t] += 1
    vecs = []
    for d in docs:
        tf = Counter(d)
        vec = {}
        for t, f in tf.items():
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            vec[t] = idf * (f * 2.5) / (f + 1.5 * (1 - 0.75 + 0.75 * len(d) / max(1, avgdl)))
        vecs.append(vec)
    out = {}
    for i in range(n):
        for j in range(i + 1, n):
            vi, vj = vecs[i], vecs[j]
            dot = sum(vi[t] * vj.get(t, 0.0) for t in vi)
            ni = math.sqrt(sum(v * v for v in vi.values()))
            nj = math.sqrt(sum(v * v for v in vj.values()))
            out[(i, j)] = dot / (ni * nj) if ni and nj else 0.0
    return out


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    out = {}
    key = None
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", line)
        if km:
            key = km.group(1)
            val = km.group(2).strip()
            out[key] = val.strip("'\"") if val else ""
        elif key and line.strip().startswith("-"):
            out.setdefault(key + "__list", []).append(line.strip()[1:].strip().strip("'\""))
    return out


def strip_fences(text: str) -> str:
    out = []
    in_fence = False
    for line in text.splitlines():
        if re.match(r"^(`{3,}|~{3,})", line):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--max-chars", type=int, default=12000)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    claude = root / ".claude"
    results = []
    failures = []

    def record(name: str, ok: bool, detail: str) -> None:
        results.append({"check": name, "ok": ok, "detail": detail})
        if not ok:
            failures.append(name)

    # 1. Byte budget
    global_md = claude / "GLOBAL_CLAUDE.md"
    gtext = global_md.read_text(encoding="utf-8") if global_md.is_file() else ""
    size = len(gtext)
    rules = [global_md, root / "CLAUDE.md"]
    if (claude / "rules").is_dir():
        rules += sorted((claude / "rules").rglob("*.md"))
    rules = [p for p in rules if p.is_file()]
    total = 0
    oversize = []
    for p in rules:
        b = len(p.read_bytes())
        total += b
        if b > 24000:
            oversize.append("%s (%d bytes)" % (p.relative_to(root), b))
    budget_ok = global_md.is_file() and size <= args.max_chars and not oversize and total <= 64000
    record("byte_budget", budget_ok, "GLOBAL_CLAUDE.md=%d/%d chars; rules total=%d/64000 bytes; oversize=%s" % (size, args.max_chars, total, oversize or "none"))

    # 2. Skill coverage & reach
    skills_dir = claude / "skills"
    skill_names = sorted(d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()) if skills_dir.is_dir() else []
    corpus = gtext
    lib = claude / "hooks" / "harness_lib.py"
    if lib.is_file():
        corpus += lib.read_text(encoding="utf-8")
    for d in (claude / "agents", claude / "commands"):
        if d.is_dir():
            for p in d.glob("*.md"):
                corpus += p.read_text(encoding="utf-8", errors="ignore")
    for idx in (root / "antigravity" / "skillbank" / "INDEX.md", root / "antigravity" / "docs" / "skill-registry.md"):
        if idx.is_file():
            corpus += idx.read_text(encoding="utf-8", errors="ignore")
    uncovered = [s for s in skill_names if s not in corpus]
    descs = []
    empty = []
    for s in skill_names:
        fm = frontmatter((skills_dir / s / "SKILL.md").read_text(encoding="utf-8", errors="ignore"))
        desc = fm.get("description", "")
        if not desc.strip():
            empty.append(s)
        descs.append(tokens("%s %s" % (fm.get("name", s), desc)))
    sims = bm25_cosine(descs)
    overlaps = []
    for (i, j), score in sims.items():
        jac = jaccard(descs[i], descs[j])
        if max(score, jac) >= 0.90:
            overlaps.append("%s~%s (%.2f)" % (skill_names[i], skill_names[j], max(score, jac)))
    record("skill_coverage", bool(skill_names) and not uncovered and not empty and not overlaps,
           "%d skills; uncovered=%s; empty_description=%s; overlap>=0.90=%s" % (len(skill_names), uncovered or "none", empty or "none", overlaps or "none"))

    # 3. Template braces
    unfenced = strip_fences(gtext)
    braces = re.findall(r"(?<!\\)\{\{|(?<!\\)\{%", unfenced)
    record("template_braces", not braces, "%d unescaped template brace(s) in GLOBAL_CLAUDE.md" % len(braces))

    # 4. Hooks / agents / commands / settings
    problems = []
    settings_path = claude / "settings.json"
    settings = {}
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception as exc:
        problems.append("settings.json invalid: %s" % exc)
    try:
        json.loads((root / ".mcp.json").read_text(encoding="utf-8"))
    except Exception as exc:
        problems.append(".mcp.json invalid: %s" % exc)
    hook_cmds = []
    for event, entries in (settings.get("hooks") or {}).items():
        for entry in entries or []:
            for h in entry.get("hooks") or []:
                cmd = str(h.get("command") or "")
                m = re.search(r"\.claude/hooks/([A-Za-z0-9_\-]+\.py)", cmd)
                if not m:
                    problems.append("%s: hook command does not reference .claude/hooks/*.py: %s" % (event, cmd))
                    continue
                hook_cmds.append(m.group(1))
                if not (claude / "hooks" / m.group(1)).is_file():
                    problems.append("%s: missing hook file %s" % (event, m.group(1)))
    sl = (settings.get("statusLine") or {}).get("command", "")
    if sl and "statusline.py" in sl and not (claude / "hooks" / "statusline.py").is_file():
        problems.append("statusLine command references missing statusline.py")
    for p in sorted((claude / "hooks").glob("*.py")) + sorted((claude / "hooks" / "tests").glob("*.py")) + sorted((root / "scripts").glob("*.py")):
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")
        except Exception as exc:
            problems.append("compile failed: %s: %s" % (p.relative_to(root), str(exc).splitlines()[-1][:120]))
    agents_dir = claude / "agents"
    agent_names = []
    if agents_dir.is_dir():
        for p in sorted(agents_dir.glob("*.md")):
            fm = frontmatter(p.read_text(encoding="utf-8", errors="ignore"))
            name = fm.get("name", "")
            agent_names.append(name)
            if name != p.stem:
                problems.append("agent %s: frontmatter name '%s' != filename" % (p.name, name))
            if not fm.get("description"):
                problems.append("agent %s: missing description" % p.name)
            model = fm.get("model", "inherit")
            if model not in ("inherit", "sonnet", "opus", "haiku", "fable") and not model.startswith("claude-"):
                problems.append("agent %s: invalid model '%s'" % (p.name, model))
            for s in fm.get("skills__list", []):
                if s not in skill_names:
                    problems.append("agent %s: preloads unknown skill '%s'" % (p.name, s))
    else:
        problems.append("missing .claude/agents")
    for required in REQUIRED_AGENTS:
        if required not in agent_names:
            problems.append("missing required agent: %s" % required)
    # MCP references in agents must resolve to servers declared in .mcp.json
    try:
        mcp_servers = set((json.loads((root / ".mcp.json").read_text(encoding="utf-8")).get("mcpServers") or {}).keys())
        for p in sorted(agents_dir.glob("*.md")) if agents_dir.is_dir() else []:
            fm = frontmatter(p.read_text(encoding="utf-8", errors="ignore"))
            for srv in re.findall(r"mcp__([A-Za-z0-9_\-]+)__", fm.get("tools", "")):
                if srv not in mcp_servers:
                    problems.append("agent %s: references MCP server '%s' not in .mcp.json" % (p.name, srv))
    except Exception as exc:
        problems.append("mcp reference check failed: %s" % exc)
    # commands must only reference agents that exist
    if (claude / "commands").is_dir():
        for p in sorted((claude / "commands").glob("*.md")):
            text = p.read_text(encoding="utf-8", errors="ignore")
            for ref in set(re.findall(r"`([a-z][a-z0-9\-]+)`", text)):
                if ref in ("dev-fe", "dev-be", "debugger", "oracle-review", "test-runner", "frontend-qc", "hallucination-auditor", "backend-explorer", "frontend-explorer", "research-explorer", "critical-planner", "doc-sync-worker", "simplifier-reviewer") and ref not in agent_names:
                    problems.append("command %s: references missing agent '%s'" % (p.name, ref))
    cmds_dir = claude / "commands"
    if cmds_dir.is_dir():
        for p in sorted(cmds_dir.glob("*.md")):
            fm = frontmatter(p.read_text(encoding="utf-8", errors="ignore"))
            if not fm.get("description"):
                problems.append("command %s: missing description" % p.name)
    else:
        problems.append("missing .claude/commands")
    for sh in sorted((root / "scripts").glob("*.sh")):
        try:
            res = subprocess.run(["bash", "-n", str(sh)], capture_output=True, text=True, timeout=10)
            if res.returncode != 0:
                problems.append("bash -n failed: %s" % sh.relative_to(root))
        except Exception:
            problems.append("bash -n error: %s" % sh.relative_to(root))
    record("hooks_agents_commands", not problems, "; ".join(problems) if problems else "%d hook commands, %d agents, %d skills ok" % (len(hook_cmds), len(agent_names), len(skill_names)))

    # 5. Security guardrail integrity (CP-2)
    pre = claude / "hooks" / "pre_tool_use.py"
    ptext = pre.read_text(encoding="utf-8", errors="ignore") if pre.is_file() else ""
    ltext = lib.read_text(encoding="utf-8", errors="ignore") if lib.is_file() else ""
    non_comment = "\n".join(l for l in ptext.splitlines() if not l.strip().startswith("#"))
    invariants = {
        "vendor_scout_block": ("node_modules" in (ptext + ltext) and "scout_blocked_dir" in ptext),
        "privacy_secret_block": ("is_privacy_blocked" in ptext and "PRIVACY_BLOCKED_BASENAMES" in ltext),
        "story_shard_lease": ("allowed_files" in ptext and "matches_allowed_file" in ptext),
        "prewrite_ast_gate": ("ast.parse(" in non_comment),
        "destructive_command_guard": ("rm\\s+" in ptext and "git\\s+reset\\s+--hard" in ptext),
        "pm_zero_code_write": ("Zero-Code-Write" in ptext),
        "settings_registers_core_hooks": all(k in (settings.get("hooks") or {}) for k in ("PreToolUse", "PostToolUse", "Stop")),
    }
    missing = [k for k, v in invariants.items() if not v]
    record("security_guardrails", not missing, "%d/%d invariants intact%s" % (len(invariants) - len(missing), len(invariants), ("; missing: %s" % missing) if missing else ""))

    if args.json:
        print(json.dumps({"ok": not failures, "results": results}, indent=2))
    else:
        for r in results:
            print("  [%s] %s: %s" % ("PASS" if r["ok"] else "FAIL", r["check"], r["detail"]))
        print("validate-claude-tree: %d/%d checks passed" % (len(results) - len(failures), len(results)))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
