#!/usr/bin/env python3
"""SubagentStart hook: injects the Turn-1 Subagent Grounding Capsule.

Carries the role persona bundle, project SOT, memory seeds, graph triples,
leased-file symbol outlines (UG-05) and the operational constraints of the
Antigravity ``_build_subagent_grounding_capsule``.
"""
from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as H  # noqa: E402
import user_prompt_submit as UPS  # noqa: E402


def fast_scan_symbols(file_path: str, max_symbols: int = 12) -> list:
    items = []
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".py":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read(400_000))
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    items.append((node.name, type(node).__name__.replace("Def", "").lower(), getattr(node, "lineno", 0), getattr(node, "end_lineno", 0)))
                if len(items) >= max_symbols:
                    break
        elif ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".kt", ".go", ".rs", ".swift", ".java"):
            pat = re.compile(r"^(?:export\s+(?:default\s+)?)?(?:async\s+)?(class|interface|type|enum|function|const|fun|fn|struct|impl)\s+([A-Za-z0-9_$]+)")
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, start=1):
                    m = pat.match(line.strip())
                    if m:
                        items.append((m.group(2), m.group(1), i, i))
                        if len(items) >= max_symbols:
                            break
    except Exception:
        pass
    return items


def leased_symbols_section(allowed: list, ws: str) -> str:
    lines = []
    for pat in allowed[:6]:
        if any(c in pat for c in "*?["):
            continue
        p = H.normalize_path(pat, ws)
        if not os.path.isfile(p):
            continue
        syms = fast_scan_symbols(p)
        if not syms:
            continue
        rel = os.path.relpath(p, ws)
        lines.append("  - %s: %s" % (rel, ", ".join("%s[%d-%d]" % (n, s, e) for n, _, s, e in syms)))
    return "- Leased File Symbol Map:\n" + "\n".join(lines) if lines else ""


def skill_paths(names: list) -> str:
    out = []
    for n in names:
        cand = H.claude_home() / "skills" / n / "SKILL.md"
        proj = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()) / ".claude" / "skills" / n / "SKILL.md"
        out.append("`%s`" % (proj if proj.is_file() else cand))
    return ", ".join(out)


def build_capsule(payload: dict) -> str:
    ws = H.workspace(payload)
    slug = H.project_slug(ws)
    role = H.role_of(payload)
    lease = H.lease_for(payload)
    prompt = str(lease.get("prompt") or "")
    allowed = list(lease.get("allowed_files") or [])
    sot = H.find_sot_docs(ws)
    mem = UPS.memory_seeds(slug, prompt, limit=4)
    ents = UPS.graph_entities(slug, prompt, limit=4)
    lines = [
        "[Subagent Turn-1 Grounding Capsule - %s]" % slug,
        "- Project SOT: prefer %s and targeted Grep before broad scanning." % (", ".join("`%s`" % s for s in sot[:2]) if sot else "targeted Grep"),
        "- Key Memory Seeds (registry.sqlite): %s" % (", ".join("`%s`" % m for m in mem) if mem else "none"),
        "- Core GraphDB Triples (graph.sqlite): %s" % ("; ".join(ents) if ents else "(none)"),
    ]
    if lease.get("has_allowed_files"):
        lines.append("- Operational Constraints: confine modifications strictly to leased `allowed_files` %s. Maintain ADHD mode (subagents exempt from rules 3, 5, 6). Return a summary only: changed files, evidence, risks, next action." % allowed)
    elif H.is_readonly_role(role):
        lines.append("- Operational Constraints: READ-ONLY role. Return coordinates (path:line), evidence and verdicts; never edit code or plans.")
    else:
        lines.append("- Operational Constraints: no `allowed_files:` lease was provided; application-code edits will be blocked. Ask the orchestrator for a lease if mutation is required.")
    bundle = H.ROLE_SKILL_BUNDLES.get(role)
    if bundle:
        lines.append("- Active Persona Bundle (`%s`): %s Reference %s if needed." % (role, bundle[1], skill_paths(list(bundle[0]))))
    if allowed:
        sec = leased_symbols_section(allowed, ws)
        if sec:
            lines.append(sec)
    capsule = "\n".join(lines)
    return capsule[:2400]


def main() -> None:
    try:
        payload = H.read_payload()
        if not payload:
            return
        if not H.is_subagent(payload):
            return
        H.claim_lease(payload)
        H.save_state(payload, "agent_meta", {
            "agent_type": payload.get("agent_type"), "agent_id": payload.get("agent_id"), "started": True,
            "transcript_path": payload.get("transcript_path"), "agent_transcript_path": payload.get("agent_transcript_path"),
            "cwd": payload.get("cwd"), "payload_keys": sorted(payload.keys()),
        }, scoped=True)
        H.emit(H.context_output("SubagentStart", build_capsule(payload)))
    except Exception:
        pass


if __name__ == "__main__":
    main()
