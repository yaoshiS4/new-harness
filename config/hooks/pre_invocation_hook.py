#!/usr/bin/env python3
"""Antigravity PreInvocation hook for dynamic workspace grounding and milestone telemetry."""
from __future__ import annotations

import collections
import functools
import glob
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

LIVE_STATE_PATH = os.path.expanduser("~/.cache/antigravity_live_state.json")


def _resolve_project_slug(workspace: str) -> str:
    if not workspace:
        workspace = os.getcwd()
    workspace = workspace.strip().strip("'\"")
    slug = os.path.basename(os.path.normpath(workspace))

    reg_db = os.path.expanduser("~/.local/share/codex/projects/registry.sqlite")
    if os.path.isfile(reg_db):
        conn = None
        try:
            conn = sqlite3.connect(f"file:{reg_db}?mode=ro", uri=True, timeout=0.5)
            conn.execute("PRAGMA busy_timeout=500;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            cur = conn.cursor()
            # Try matching by project_path
            try:
                row = cur.execute(
                    "SELECT slug FROM projects WHERE project_path = ? OR project_path LIKE ? LIMIT 1;",
                    (workspace, f"%{slug}%"),
                ).fetchone()
            except Exception:
                row = cur.execute(
                    "SELECT slug FROM projects WHERE path = ? OR path LIKE ? LIMIT 1;",
                    (workspace, f"%{slug}%"),
                ).fetchone()
            if row and row[0]:
                slug = row[0]
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    return slug


def _get_cue_matched_memory_keys(slug: str, prompt_text: str = "", limit: int = 4) -> list[str]:
    reg_db = os.path.expanduser("~/.local/share/codex/projects/registry.sqlite")
    if not os.path.isfile(reg_db):
        return []

    conn = None
    try:
        conn = sqlite3.connect(f"file:{reg_db}?mode=ro", uri=True, timeout=0.5)
        conn.execute("PRAGMA busy_timeout=500;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT key, value FROM memory WHERE slug = ? ORDER BY id DESC LIMIT 25;",
            (slug,),
        ).fetchall()
        if not rows:
            return []

        prompt_keywords = {k.lower() for k in _extract_prompt_keywords(prompt_text)} if prompt_text else set()
        if prompt_keywords:
            scored: list[tuple[int, int, str]] = []
            for idx, (k, v) in enumerate(rows):
                if not k:
                    continue
                k_text = str(k).lower()
                v_text = str(v or "").lower()
                row_tokens = set(re.findall(r"[a-z0-9]{2,}", f"{k_text} {v_text}"))
                row_tokens.update(re.findall(r"[a-z0-9_\-\.]{2,}", f"{k_text} {v_text}"))
                overlap = len(prompt_keywords.intersection(row_tokens))
                scored.append((-overlap, str(k), idx))

            scored.sort()
            if scored and scored[0][0] < 0:
                result = [item[1] for item in scored if item[0] < 0][:limit]
                if len(result) < limit:
                    for k, _ in sorted(rows, key=lambda r: str(r[0])):
                        if k and str(k) not in result:
                            result.append(str(k))
                            if len(result) >= limit:
                                break
                return result

        return [str(r[0]) for r in rows if r[0]][:limit]
    except Exception:
        return []
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def _classify_graph_intent(prompt_text: str) -> dict[str, float]:
    p = (prompt_text or "").lower()
    if re.search(r"\b(fix|bug|error|fail|broken|crash|loop|issue|jev)\b", p):
        return {"causal": 1.8, "episodic": 1.4, "temporal": 1.1, "semantic": 0.9}
    if re.search(r"\b(when|history|timeline|previous|superseded)\b", p):
        return {"temporal": 1.8, "episodic": 1.5, "causal": 1.1, "semantic": 0.9}
    return {"semantic": 1.5, "causal": 1.2, "temporal": 1.0, "episodic": 0.9}


def _traverse_seeded_subgraph(
    graph_db: str,
    prompt_text: str = "",
    allowed_files: list[str] | None = None,
    limit: int = 4,
) -> list[tuple[str, str, str, str]]:
    if not graph_db or not os.path.isfile(graph_db):
        return []

    conn = None
    try:
        try:
            conn = sqlite3.connect(f"file:{graph_db}?mode=ro", uri=True, timeout=0.5)
        except Exception:
            conn = sqlite3.connect(graph_db, timeout=0.5)
        conn.execute("PRAGMA busy_timeout=500;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        cur = conn.cursor()

        # Verify edges table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='edges' LIMIT 1;")
        if not cur.fetchone():
            return []

        cols = {r[1] for r in cur.execute("PRAGMA table_info(edges);").fetchall()}
        has_layer = "layer" in cols
        has_is_current = "is_current" in cols
        has_valid_to = "valid_to" in cols
        has_invalidated_at = "invalidated_at" in cols

        conds = []
        if has_is_current:
            conds.append("is_current = 1")
        if has_valid_to:
            conds.append("(valid_to IS NULL OR valid_to = '')")
        if has_invalidated_at:
            conds.append("(invalidated_at IS NULL OR invalidated_at = '')")
        where_sql = f"WHERE {' AND '.join(conds)}" if conds else ""

        layer_col = "layer" if has_layer else "'semantic' AS layer"
        query = (
            f"SELECT src, rel, dst, {layer_col} FROM edges {where_sql} "
            "ORDER BY (CASE WHEN rel = 'CALLED_TOOL' OR src LIKE 'tool:%' OR dst LIKE 'tool:%' THEN 1 ELSE 0 END) ASC "
            "LIMIT 500;"
        )
        rows = cur.execute(query).fetchall()
        if not rows:
            return []

        all_active_edges: list[tuple[str, str, str, str]] = [
            (str(r[0]), str(r[1]), str(r[2]), str(r[3] or "semantic"))
            for r in rows
            if r[0] and r[2]
        ]
        if not all_active_edges:
            return []

        filtered_edges: list[tuple[str, str, str, str]] = [
            edge
            for edge in all_active_edges
            if edge[1] != "CALLED_TOOL"
            and not edge[0].startswith("tool:")
            and not edge[2].startswith("tool:")
        ]
        active_edges = filtered_edges if filtered_edges else all_active_edges

        # Stage 1: Entrypoint Seed Retrieval
        prompt_kws = {k.lower() for k in _extract_prompt_keywords(prompt_text)} if prompt_text else set()
        file_kws: set[str] = set()
        if allowed_files:
            for f in allowed_files:
                if f:
                    base = os.path.basename(f).lower()
                    file_kws.add(base)
                    stem, _ = os.path.splitext(base)
                    if stem:
                        file_kws.add(stem)
        seed_tokens = prompt_kws | file_kws

        out_degrees: collections.Counter[str] = collections.Counter()
        in_degrees: collections.Counter[str] = collections.Counter()
        all_nodes: set[str] = set()
        for src, rel, dst, _ in active_edges:
            out_degrees[src] += 1
            in_degrees[dst] += 1
            all_nodes.add(src)
            all_nodes.add(dst)

        scored_seeds: list[tuple[float, int, str]] = []
        if seed_tokens:
            for node in all_nodes:
                node_lower = node.lower()
                lex_score = 0.0
                for tok in seed_tokens:
                    if tok == node_lower:
                        lex_score += 3.0
                    elif tok in node_lower:
                        lex_score += 1.5
                if lex_score > 0:
                    total_score = lex_score * 10.0 + out_degrees[node] * 1.0 + in_degrees[node] * 0.5
                    scored_seeds.append((total_score, out_degrees[node], node))
            scored_seeds.sort(key=lambda x: (-x[0], -x[1], x[2]))

        seeds: list[str] = [s[2] for s in scored_seeds[:4]]

        if not seeds:
            # Fallback when no lexical match or prompt_text is empty
            prioritized_rels = {
                "NAVIGATES_TO", "PROVIDES", "IMPLEMENTS", "MODIFIED_IN",
                "CAUSED_BY", "EXTENDS", "APPLIES_TO"
            }
            rel_candidates = [
                src for src, rel, dst, _ in active_edges if rel in prioritized_rels
            ]
            seen_cand = set()
            for cand in sorted(rel_candidates, key=lambda n: (-out_degrees[n], n)):
                if cand not in seen_cand:
                    seen_cand.add(cand)
                    seeds.append(cand)
                    if len(seeds) >= 4:
                        break
            if not seeds:
                for node in sorted(all_nodes, key=lambda n: (-out_degrees[n], n))[:4]:
                    seeds.append(node)
            if not seeds:
                seeds = sorted(all_nodes)[:4]

        # Stage 2: Constrained 2-Hop Traversal + Intent Layer Ranking
        intent_weights = _classify_graph_intent(prompt_text)
        edge_scores: dict[tuple[str, str, str, str], float] = {}
        hop1_nodes: set[str] = set()
        seed_set = set(seeds)

        # Hop 1
        for edge in active_edges:
            src, rel, dst, layer = edge
            if src in seed_set or dst in seed_set:
                hop_decay = 1.0
                layer_w = intent_weights.get(layer, 1.0)
                kw_boost = 1.5 if (prompt_kws and (any(k in src.lower() for k in prompt_kws) or any(k in dst.lower() for k in prompt_kws))) else 1.0
                edge_scores[edge] = hop_decay * layer_w * kw_boost
                hop1_nodes.add(src)
                hop1_nodes.add(dst)

        # Hop 2
        hop2_seeds = hop1_nodes - seed_set
        for edge in active_edges:
            if edge not in edge_scores:
                src, rel, dst, layer = edge
                if src in hop2_seeds or dst in hop2_seeds:
                    hop_decay = 0.6
                    layer_w = intent_weights.get(layer, 1.0)
                    kw_boost = 1.5 if (prompt_kws and (any(k in src.lower() for k in prompt_kws) or any(k in dst.lower() for k in prompt_kws))) else 1.0
                    edge_scores[edge] = hop_decay * layer_w * kw_boost

        if not edge_scores:
            for edge in active_edges[:limit]:
                edge_scores[edge] = 1.0

        ranked_edges = sorted(
            edge_scores.keys(),
            key=lambda e: (-edge_scores[e], -out_degrees[e[0]], str(e)),
        )
        return ranked_edges[:limit]
    except Exception:
        return []
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def _get_dynamic_seeds(slug: str, prompt_text: str = "") -> tuple[list[str], list[str]]:
    memories: list[str] = _get_cue_matched_memory_keys(slug, prompt_text, limit=4)
    graph_entities: list[str] = []

    graph_db = os.path.expanduser(f"~/.local/share/codex/projects/{slug}/graph/graph.sqlite")
    if os.path.isfile(graph_db):
        subgraph = _traverse_seeded_subgraph(graph_db, prompt_text=prompt_text, limit=4)
        if prompt_text:
            graph_entities = [f"({src}) -[{rel}]-> ({dst})" for src, rel, dst, _ in subgraph]
        else:
            seen = set()
            for src, _, _, _ in subgraph:
                if src not in seen:
                    seen.add(src)
                    graph_entities.append(src)

    return memories, graph_entities


def _get_subagent_graph_triples(
    slug: str,
    prompt_text: str = "",
    allowed_files: list[str] | None = None,
) -> list[str]:
    triples: list[str] = []
    graph_db = os.path.expanduser(f"~/.local/share/codex/projects/{slug}/graph/graph.sqlite")
    if not os.path.isfile(graph_db):
        return triples

    subgraph = _traverse_seeded_subgraph(
        graph_db,
        prompt_text=prompt_text,
        allowed_files=allowed_files,
        limit=3,
    )
    for src, rel, dst, _ in subgraph:
        triples.append(f"({src}) -[{rel}]-> ({dst})")
    return triples


def _get_subagent_memory_keys(slug: str, prompt_text: str = "") -> list[str]:
    return _get_cue_matched_memory_keys(slug, prompt_text, limit=3)


def _extract_allowed_files(text: str) -> list[str]:
    if not text or "allowed_files" not in text:
        return []
    m = re.search(r'(?:^|\n|\b)[ \t]*[`*_-]*allowed_files[`*_-]*\s*:\s*(.*)', text, re.IGNORECASE)
    if not m:
        return []

    rest = text[m.start():].strip()

    # Try YAML parsing first if yaml is available
    try:
        import yaml
        lines = []
        for i, line in enumerate(rest.splitlines()):
            if i == 0:
                lines.append(line)
            else:
                if re.match(r'^[A-Za-z0-9_-]+:', line) or re.match(r'^[#*]{2,}', line):
                    break
                lines.append(line)
        parsed = yaml.safe_load('\n'.join(lines))
        if isinstance(parsed, dict):
            for k, v in parsed.items():
                if 'allowed_files' in str(k).lower():
                    if isinstance(v, list):
                        files = [str(x).strip() for x in v if x is not None]
                        return [f for f in files if "*" not in f and "?" not in f]
                    elif isinstance(v, str) and v.strip():
                        return [v.strip()] if "*" not in v and "?" not in v else []
                    elif v is None:
                        return []
    except Exception:
        pass

    # Fallback JSON / regex extraction
    line_rest = m.group(1).strip()
    if line_rest.startswith('['):
        arr_m = re.search(r'\[(.*?)\]', rest, re.DOTALL)
        if arr_m:
            try:
                items = json.loads('[' + arr_m.group(1) + ']')
                files = [str(x).strip() for x in items if x is not None]
            except Exception:
                files = [x.strip(' \'"') for x in arr_m.group(1).split(',') if x.strip(' \'"')]
            return [f for f in files if "*" not in f and "?" not in f]

    # Fallback bullet lines
    files = []
    for line in rest.splitlines()[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(('-', '*')):
            val = stripped[1:].strip().strip('\'"`')
            if val and not val.startswith('#'):
                files.append(val)
        elif re.match(r'^[A-Za-z0-9_-]+:', stripped) or re.match(r'^[#*]{2,}', stripped):
            break
    return [f for f in files if "*" not in f and "?" not in f]


def _strip_user_request_tags(text: str) -> str:
    if not text:
        return ""
    if "<USER_REQUEST>" in text:
        m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", text, re.DOTALL)
        if m:
            return m.group(1).strip()
        return text.split("<USER_REQUEST>", 1)[1].strip()
    return text.strip()


def _resolve_conv_id(payload: dict) -> str:
    conv_id = str(payload.get("conversationId") or "").strip()
    if not conv_id:
        transcript_p = str(payload.get("transcriptPath") or "").strip()
        if transcript_p:
            m_cid = re.search(r"/brain/([a-f0-9\-]+)/", transcript_p)
            if m_cid:
                conv_id = m_cid.group(1)
    return conv_id


def _iter_candidate_transcript_paths(payload: dict) -> list[Path]:
    paths: list[Path] = []
    seen: set[str] = set()
    tp_raw = str(payload.get("transcriptPath") or "").strip()
    if tp_raw:
        tp = Path(tp_raw).expanduser()
        if tp.is_file():
            resolved = str(tp)
            seen.add(resolved)
            paths.append(tp)

    conv_id = _resolve_conv_id(payload)
    if conv_id:
        for root in (
            "~/.gemini/antigravity-cli/brain",
            "~/.gemini/antigravity-ide/brain",
            "~/.gemini/antigravity/brain",
        ):
            cand = Path(f"{root}/{conv_id}/.system_generated/logs/transcript.jsonl").expanduser()
            if cand.is_file():
                resolved = str(cand)
                if resolved not in seen:
                    seen.add(resolved)
                    paths.append(cand)
    return paths


def _has_any_user_turn_evidence(payload: dict) -> bool:
    for key in ("lastUserInput", "userPrompt", "prompt"):
        val = payload.get(key)
        if isinstance(val, str) and _strip_user_request_tags(val):
            return True

    steps = payload.get("transcript")
    if isinstance(steps, list):
        if any(isinstance(s, dict) and s.get("type") == "USER_INPUT" for s in steps):
            return True

    for tp in _iter_candidate_transcript_paths(payload):
        try:
            with open(tp, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        if isinstance(obj, dict) and obj.get("type") == "USER_INPUT":
                            return True
                    except Exception:
                        if re.search(r'"type"\s*:\s*"USER_INPUT"', line):
                            return True
        except Exception:
            pass
    return False


def _is_system_sdk_or_grounding_step(data: dict) -> bool:
    if not isinstance(data, dict):
        return False
    if data.get("source") == "SYSTEM_SDK":
        return True
    c = _strip_user_request_tags(str(data.get("content", ""))).lstrip()
    if c.startswith(("[Session Grounding Anchor]", "[Session Grounding Anchor", "[Active Knowledge Grounding")):
        return True
    return False


def _extract_initial_subagent_prompt(payload: dict) -> str:
    for k in ("lastUserInput", "userPrompt", "prompt", "systemMessage", "initialPrompt"):
        val = payload.get(k)
        if isinstance(val, str) and val.strip():
            cleaned = _strip_user_request_tags(val)
            if "allowed_files" in cleaned:
                return cleaned

    steps = payload.get("transcript")
    if isinstance(steps, list):
        for s in steps[:6]:
            if isinstance(s, dict):
                if _is_system_sdk_or_grounding_step(s):
                    continue
                c = _strip_user_request_tags(str(s.get("content", "")))
                if "allowed_files" in c or s.get("type") == "SYSTEM_MESSAGE":
                    return c

    for tp in _iter_candidate_transcript_paths(payload):
        try:
            with open(tp, "r", encoding="utf-8", errors="ignore") as f:
                scanned = 0
                for raw_line in f:
                    line = raw_line.strip()
                    if not line:
                        continue
                    scanned += 1
                    if scanned > 6:
                        break
                    try:
                        data = json.loads(line)
                        if not isinstance(data, dict):
                            continue
                        if _is_system_sdk_or_grounding_step(data):
                            continue
                        c = _strip_user_request_tags(str(data.get("content", "")))
                        if "allowed_files" in c or data.get("type") == "SYSTEM_MESSAGE":
                            return c
                    except Exception:
                        pass
        except Exception:
            pass

    last_input = payload.get("lastUserInput")
    if isinstance(last_input, str) and last_input.strip():
        cleaned = _strip_user_request_tags(last_input)
        if cleaned:
            return cleaned
    return ""


def _fast_scan_symbols(file_path: str, max_symbols: int = 12) -> list[tuple[str, str, int, int]]:
    if not os.path.isfile(file_path):
        return []
    symbols: list[tuple[str, str, int]] = []
    pattern = re.compile(
        r"^(?:export\s+(?:default\s+)?)?(?:async\s+)?(def|class|function|const|let|var|type|interface|enum)\s+([A-Za-z0-9_]+)"
    )
    try:
        raw_lines = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f, 1):
                raw_lines.append(idx)
                m = pattern.match(line)
                if m:
                    kind = m.group(1)
                    name = m.group(2)
                    symbols.append((name, kind, idx))
                    if len(symbols) >= max_symbols:
                        break
        total = len(raw_lines)
        res: list[tuple[str, str, int, int]] = []
        for i, (name, kind, start) in enumerate(symbols):
            end = symbols[i + 1][2] - 1 if (i + 1 < len(symbols)) else total
            res.append((name, kind, start, max(start, end)))
        return res
    except Exception:
        return []


def _get_symbols_for_leased_file(file_path: str, workspace: str, max_symbols: int = 12) -> list[tuple[str, str, int, int]]:
    db_path = os.path.expanduser("~/.local/share/codex/codegraph_index.sqlite")
    if os.path.isfile(db_path):
        conn = None
        try:
            rel_path = ""
            if workspace:
                try:
                    rel_path = os.path.relpath(file_path, workspace)
                except Exception:
                    rel_path = ""
            candidates = [file_path]
            if rel_path and rel_path != file_path and not rel_path.startswith(".."):
                candidates.append(rel_path)

            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=0.1)
            cur = conn.cursor()
            cols = []
            try:
                cols = [r[1] for r in cur.execute("PRAGMA table_info(symbols);").fetchall()]
            except Exception:
                pass
            has_workspace = "workspace" in cols

            for cand in candidates:
                if has_workspace and workspace:
                    rows = cur.execute(
                        "SELECT name, kind, line, end_line FROM symbols WHERE path = ? AND workspace = ? AND exported = 1 LIMIT ?;",
                        (cand, workspace, max_symbols),
                    ).fetchall()
                else:
                    rows = cur.execute(
                        "SELECT name, kind, line, end_line FROM symbols WHERE path = ? AND exported = 1 LIMIT ?;",
                        (cand, max_symbols),
                    ).fetchall()
                if rows:
                    return [(r[0], r[1], int(r[2]), int(r[3])) for r in rows]
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    abs_path = file_path
    if not os.path.isabs(abs_path) and workspace:
        abs_path = os.path.join(workspace, file_path)
    return _fast_scan_symbols(abs_path, max_symbols=max_symbols)


def _build_leased_symbols_section(allowed_files: list[str], workspace: str) -> str:
    if not allowed_files:
        return ""
    file_entries: list[str] = []
    target_files = sorted(set(allowed_files))[:4]
    per_file_cap = max(3, 12 // len(target_files)) if target_files else 3

    for fpath in target_files:
        syms = _get_symbols_for_leased_file(fpath, workspace, max_symbols=per_file_cap)
        fname = os.path.basename(fpath)
        if syms:
            sym_strs = []
            for name, kind, start, end in syms:
                if end > start:
                    sym_strs.append(f"`{name}` ({kind}, L{start}-L{end})")
                else:
                    sym_strs.append(f"`{name}` ({kind}, L{start})")
            file_entries.append(f"  - {fname}: " + ", ".join(sym_strs))
        else:
            file_entries.append(f"  - {fname}: (no exported symbols indexed)")

    if not file_entries:
        return ""
    return "- Leased File Symbols:\n" + "\n".join(file_entries)


ROLE_SKILL_BUNDLES: dict[str, tuple[str | list[str], str]] = {
    "pm": ("~/.gemini/antigravity/skills/routing-thresholds/SKILL.md", "PM Orchestrator: Classify complexity, emit Story Shards, never mutate application code."),
    "sa": ("~/.gemini/antigravity/skills/senior-architect/SKILL.md", "Senior Architect: Define interfaces, ADRs, and bounded contracts before implementation."),
    "senior-architect": ("~/.gemini/antigravity/skills/senior-architect/SKILL.md", "Senior Architect: Define interfaces, ADRs, and bounded contracts before implementation."),
    "critical-planner": ("~/.gemini/antigravity/skills/senior-architect/SKILL.md", "Critical Planner: Conduct adversarial plan review and challenge assumptions."),
    "critique": ("~/.gemini/antigravity/skills/senior-architect/SKILL.md", "Critical Planner: Conduct adversarial plan review and challenge assumptions."),
    "dev-fe": ("~/.gemini/antigravity/skills/ui-ux-craft/SKILL.md", "Frontend Builder: Reuse shared design tokens, make surgical UI diffs, and satisfy anti-slop invariants."),
    "dev-be": (["oracle-review", "auto-verification-harness"], "Backend Builder: Apply verification-before-completion and structured validation to backend changes."),
    "designer": ("~/.gemini/antigravity/skills/ui-ux-craft/SKILL.md", "UI/UX Designer: Enforce visual hierarchy, token compliance, and anti-slop layout rules."),
    "visual-engineer": (["ui-ux-craft", "ui-ux-audit"], "Visual Engineer: UI/UX design tokens, layout ergonomics, animations, and anti-slop audit."),
    "frontend-qc": ("~/.gemini/antigravity/skills/ui-ux-audit/SKILL.md", "Frontend QC: Read-only inspector. Audit UI against anti-slop taxonomy (L-01, L-13, T-12, D-09)."),
    "debugger": ("~/.gemini/antigravity/skills/auto-verification-harness/SKILL.md", "Debugger: Reproduce failures on the smallest surface and trace root-cause evidence before patching."),
    "oracle-review": ("~/.gemini/antigravity/skills/oracle-review/SKILL.md", "Oracle Reviewer: Read-only audit for regressions, scope drift, hallucinated references, and missing tests."),
    "hallucination-auditor": ("~/.gemini/antigravity/skills/oracle-review/SKILL.md", "Hallucination Auditor: Verify all file paths, symbols, and execution claims against ground truth."),
    "implementation-review": (["oracle-review", "auto-verification-harness"], "Implementation Reviewer: Independent audit of code changes, verification, and regression control."),
    "simplifier-reviewer": (["oracle-review", "scope-drift-control"], "Simplifier Reviewer: Scope drift control and anti-complexity code simplification review."),
    "test-runner": (["e2e_testing", "auto-verification-harness"], "Test Runner: Dynamic test execution, structured validation, and verification logging."),
    "user-tester": (["e2e_testing", "auto-verification-harness"], "User Tester: End-to-end user journey validation and test suite execution."),
    "devops": (["auto-verification-harness"], "DevOps: Build harness verification, test harnesses, and environment validation."),
    "meta-evolution": (["harness-deficiency-audit"], "Meta Evolution: Optimize agent skills and audit harness deficiencies."),
    "skillopt-optimizer": (["harness-deficiency-audit"], "Skill Optimizer: Optimize skill documents with bounded edits and held-out validation."),
    "librarian": (["document-sync", "sot-context"], "Librarian: Documentation sync, knowledge capture, and SOT grounding."),
    "diff-helper": (["scope-drift-control", "auto-verification-harness"], "Diff Helper: Scope drift control and structured diff validation."),
    "whitehat": ("~/.gemini/antigravity/skills/security-audit/SKILL.md", "Security Auditor: Read-only check of auth, secrets, command execution, and trust boundaries."),
    "security-audit": ("~/.gemini/antigravity/skills/security-audit/SKILL.md", "Security Auditor: Read-only check of auth, secrets, command execution, and trust boundaries."),
    "backend-explorer": ("~/.gemini/antigravity/skills/codegraph-explorer/SKILL.md", "Backend Explorer: Read-only CodeGraph-first discovery of services, schemas, and APIs."),
    "frontend-explorer": ("~/.gemini/antigravity/skills/codegraph-explorer/SKILL.md", "Frontend Explorer: Read-only CodeGraph-first discovery of components, state, and routes."),
    "research-explorer": ("~/.gemini/antigravity/skills/ground-truth-retrieval/SKILL.md", "Research Explorer: Read-only external documentation and Context7 verification."),
    "doc-sync-worker": ("~/.gemini/antigravity/skills/document-sync/SKILL.md", "Doc Sync Worker: Synchronize approved changes into docs/STATUS.md and codex_knowledge."),
    "browseros-neo": ("~/.gemini/config/skills/browseros-neo/SKILL.md", "BrowserOS Neo: Dedicated real browser with live logins, automation, and persistent session state."),
    "browser": ("~/.gemini/config/skills/browseros-neo/SKILL.md", "BrowserOS Neo: Dedicated real browser with live logins, automation, and persistent session state."),
    "meta-invariant-editor": (["harness-deficiency-audit", "auto-verification-harness"], "Meta Invariant Editor (INV): Mechanically leased to tool-quirks, guardrails, and subagent topology. Forbidden from mutating application code or domain skills."),
    "meta-domain-editor": (["harness-deficiency-audit", "auto-verification-harness"], "Meta Domain Editor (DOM): Mechanically leased to task_harness/SKILL.md and scripts/verify_task.py. Forbidden from mutating global hooks or rules."),
}


def _detect_subagent_role_directive(init_prompt: str, payload: dict | None) -> str:
    role_cand = ""
    if payload:
        role_cand = str(payload.get("role") or payload.get("agentRole") or "").strip().lower()
    if not role_cand and init_prompt:
        m = re.search(r"\brole\s*[:=]\s*['\"]?([a-z0-9_-]+)['\"]?", init_prompt, re.IGNORECASE)
        if m:
            role_cand = m.group(1).strip().lower()
        else:
            prompt_lower = init_prompt.lower()
            for r_key in ROLE_SKILL_BUNDLES:
                if f"role: {r_key}" in prompt_lower or f"as `{r_key}`" in prompt_lower or f"({r_key})" in prompt_lower:
                    role_cand = r_key
                    break
    if role_cand in ROLE_SKILL_BUNDLES:
        skill_ref, desc = ROLE_SKILL_BUNDLES[role_cand]
        if isinstance(skill_ref, (list, tuple)):
            skill_paths = ", ".join(
                f"`~/.gemini/antigravity/skills/{s}/SKILL.md`" if not s.startswith("~") else f"`{s}`"
                for s in skill_ref
            )
            return f"\n- Active Persona Bundle (`{role_cand}`): {desc} Reference {skill_paths} if needed."
        return f"\n- Active Persona Bundle (`{role_cand}`): {desc} Reference `{skill_ref}` if needed."
    return ""


def _find_existing_sot_docs(workspace: str) -> list[str]:
    """Finds existing project-local SOT docs in order of priority:
    docs/STATUS.md, docs/README.md, AGENTS.md, README.md.
    Returns relative paths of existing files.
    """
    if not workspace or not os.path.isdir(workspace):
        return []
    candidates = ["docs/STATUS.md", "docs/README.md", "AGENTS.md", "README.md"]
    existing = []
    for cand in candidates:
        if os.path.isfile(os.path.join(workspace, cand)):
            existing.append(cand)
    return existing


def _build_subagent_grounding_capsule(slug: str, workspace: str, payload: dict | None = None) -> str:
    init_prompt = ""
    role_directive_block = ""
    leased_symbols_block = ""
    allowed: list[str] = []
    if payload:
        init_prompt = _extract_initial_subagent_prompt(payload)
        role_directive_block = _detect_subagent_role_directive(init_prompt, payload)
        allowed = _extract_allowed_files(init_prompt)
        if allowed:
            sec = _build_leased_symbols_section(allowed, workspace)
            if sec:
                leased_symbols_block = f"\n{sec}"

    triples = _get_subagent_graph_triples(slug, prompt_text=init_prompt, allowed_files=allowed)
    memories = _get_subagent_memory_keys(slug, init_prompt)

    sot_files = _find_existing_sot_docs(workspace)
    sot_hint = f" (consult {sot_files[0]})" if sot_files else ""
    mem_str = ", ".join(f"`{m}`" for m in memories) if memories else f"none{sot_hint}"
    if triples:
        triples_block = "\n".join(f"  - {t}" for t in triples)
    else:
        triples_block = "  - (No active triples in graph.sqlite)"

    if sot_files:
        sot_cite = ", ".join(f"`{s}`" for s in sot_files[:2])
        sot_line = f"- Project SOT: Prefer {sot_cite} and targeted ripgrep before broad scanning.\n"
    else:
        sot_line = "- Project SOT: Prefer targeted ripgrep before broad scanning.\n"

    capsule = (
        f"[Subagent Turn-1 Grounding Capsule - {slug}]\n"
        f"{sot_line}"
        f"- Key Memory Seeds (registry.sqlite): {mem_str}\n"
        f"- Core GraphDB Triples (graph.sqlite, is_current=1):\n{triples_block}\n"
        f"- Operational Constraints: Confine modifications strictly to leased `allowed_files`. Maintain ADHD mode."
        f"{role_directive_block}"
        f"{leased_symbols_block}"
    )
    return capsule


def _auto_ensure_verification_gates(workspace: str) -> bool:
    try:
        # Opt-in safety gate: Never silently scaffold files into foreign repositories unless explicitly requested
        if os.environ.get("AUTO_VERIFY_GATES") != "1":
            return False

        wp = Path(workspace).resolve()
        if not wp.is_dir():
            return False

        oracle_sh = wp / "scripts" / "verification" / "verify-oracle.sh"
        test3_sh = wp / "scripts" / "verification" / "test-3-round-loop.sh"

        if oracle_sh.is_file() and test3_sh.is_file():
            return True

        # Check if workspace is a project/repo
        is_project = (
            (wp / ".git").exists()
            or (wp / "package.json").is_file()
            or (wp / "pyproject.toml").is_file()
            or (wp / "Cargo.toml").is_file()
            or (wp / "AGENTS.md").is_file()
            or (wp / "CMakeLists.txt").is_file()
            or (wp / "go.mod").is_file()
        )
        if not is_project:
            return False

        scaffolder_path = Path(os.path.expanduser("~/.gemini/antigravity/scripts/ensure-verification-gates.py"))
        if scaffolder_path.is_file():
            import importlib.util
            spec = importlib.util.spec_from_file_location("ensure_verification_gates", str(scaffolder_path))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "ensure_repo_gates"):
                    mod.ensure_repo_gates(wp)
                    return True
        return oracle_sh.is_file() and test3_sh.is_file()
    except Exception:
        return False


def _is_subagent_conversation(payload: dict) -> bool:
    if payload.get("is_subagent") is True or payload.get("subagentRole") or payload.get("parentConversationId"):
        return True
    if str(payload.get("agentRole", "")).lower() in ("dev-fe", "dev-be", "debugger", "frontend-qc", "test-runner", "builder", "explorer"):
        return True
    if "transcript" in payload and isinstance(payload["transcript"], list) and payload["transcript"]:
        steps = [
            s for s in payload["transcript"]
            if isinstance(s, dict) and not _is_system_sdk_or_grounding_step(s)
        ]
        if steps:
            has_user_input = any(s.get("type") == "USER_INPUT" for s in steps)
            if not has_user_input:
                return True

    for tp in _iter_candidate_transcript_paths(payload):
        try:
            has_lines = False
            has_user_input = False
            with open(tp, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        if isinstance(obj, dict):
                            if _is_system_sdk_or_grounding_step(obj):
                                continue
                            has_lines = True
                            if obj.get("type") == "USER_INPUT":
                                has_user_input = True
                                break
                    except Exception:
                        has_lines = True
                        if re.search(r'"type"\s*:\s*"USER_INPUT"', line):
                            has_user_input = True
                            break
            if has_lines and not has_user_input:
                return True
        except Exception:
            pass
    return False


def _find_active_plan(payload: dict, workspace: str) -> Path | None:
    candidates: list[Path] = []
    art_dir = payload.get("artifactDirectoryPath")
    if art_dir:
        candidates.append(Path(art_dir) / "implementation_plan.md")

    conv_id = payload.get("conversationId")
    if conv_id:
        for root in (
            "~/.gemini/antigravity-ide/brain",
            "~/.gemini/antigravity/brain",
            "~/.gemini/antigravity-cli/brain",
        ):
            candidates.append(Path(f"{root}/{conv_id}/implementation_plan.md").expanduser())

    now = time.time()
    for cand in candidates:
        if cand.is_file():
            return cand

    if workspace:
        ws_plan = Path(workspace) / "implementation_plan.md"
        if ws_plan.is_file():
            try:
                if (now - os.path.getmtime(ws_plan)) <= 1800:
                    return ws_plan
            except Exception:
                pass

    return None


def _is_plan_oracle_verified(plan_file: Path) -> bool:
    try:
        content = plan_file.read_text(encoding="utf-8", errors="ignore")
        if len(content.strip()) < 20:
            return True  # Empty/uninitialized scratch file, skip
        return (
            "## Oracle Hardening" in content
            or "ORACLE REVIEW GATEWAY SIGN-OFF" in content
            or "## 8. Oracle Hardening" in content
        )
    except Exception:
        return False


def _should_suppress_watchdog(plan_path: Path) -> bool:
    try:
        plan_str = str(plan_path.resolve())
        mtime = os.path.getmtime(plan_str)
        plan_hash = hashlib.sha256(f"{plan_str}:{mtime}".encode()).hexdigest()[:16]
        state_file = Path(tempfile.gettempdir()) / f".oracle_watchdog_{plan_hash}"
        if state_file.is_file():
            return True
        state_file.touch()
        return False
    except Exception:
        return False


def _find_unverified_plan(payload: dict, workspace: str) -> Path | None:
    plan = _find_active_plan(payload, workspace)
    if plan and not _is_plan_oracle_verified(plan):
        return plan
    return None


def _check_and_consume_syntax_warning(payload: dict, workspace: str = "") -> str:
    art_dir = payload.get("artifactDirectoryPath")
    candidates: list[Path] = []
    if art_dir:
        candidates.append(Path(art_dir) / "syntax_error_pending.json")
    conv_id = payload.get("conversationId")
    if conv_id:
        for root in (
            "~/.gemini/antigravity-ide/brain",
            "~/.gemini/antigravity/brain",
            "~/.gemini/antigravity-cli/brain",
        ):
            candidates.append(Path(f"{root}/{conv_id}/syntax_error_pending.json").expanduser())
    if workspace:
        ws_hash = hashlib.sha256(str(Path(workspace).resolve()).encode()).hexdigest()[:12]
        candidates.append(Path(tempfile.gettempdir()) / f".antigravity_syntax_error_{ws_hash}.json")

    found_data = None
    for cand in candidates:
        if cand.is_file():
            try:
                if found_data is None:
                    found_data = json.loads(cand.read_text(encoding="utf-8"))
                cand.unlink(missing_ok=True)
            except Exception:
                pass
    if found_data:
        if found_data.get("delivered_inline") is True:
            return ""
        fn = found_data.get("file", "unknown")
        err = found_data.get("error", "syntax error")
        kind = found_data.get("kind", "syntax")
        if kind == "quality":
            return (
                f"[Quality Warning] Quality issue detected immediately after editing `{os.path.basename(fn)}`:\n"
                f"{err}\n"
                "Please address these quality warnings before completing your turn."
            )
        return (
            f"[SWE-Agent Syntax Smoke Alert] Broken syntax detected immediately after editing `{os.path.basename(fn)}`:\n"
            f"{err}\n"
            "You MUST fix this syntax error before running tests or completing your turn."
        )
    return ""


def _get_latest_user_prompt(payload: dict) -> str:
    for key in ("lastUserInput", "userPrompt", "prompt"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            cleaned = _strip_user_request_tags(val)
            if cleaned:
                return cleaned
    for transcript_path in _iter_candidate_transcript_paths(payload):
        try:
            fsize = transcript_path.stat().st_size
            seek_pos = max(0, fsize - 256 * 1024)
            with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                if seek_pos > 0:
                    f.seek(seek_pos)
                    f.readline()  # discard possible partial line
                lines = f.readlines()
                for line in reversed(lines):
                    try:
                        data = json.loads(line)
                        if data.get("type") == "USER_INPUT":
                            c = _strip_user_request_tags(str(data.get("content", "")))
                            if c:
                                return c
                    except Exception:
                        pass
        except Exception:
            pass
    return ""


def _ensure_cli_statusline_and_yolo_settings(payload: dict | None = None) -> None:
    if isinstance(payload, dict):
        surface_val = str(payload.get("surface") or "").strip().lower()
        raw_client = payload.get("client")
        client_val = (
            json.dumps(raw_client).lower()
            if isinstance(raw_client, (dict, list))
            else str(raw_client or "").strip().lower()
        )
        transcript_p = str(payload.get("transcriptPath") or "").lower()
        app_data_dir = str(payload.get("appDataDir") or "").lower()
        if (
            re.search(r"(?:^|[-_\s/\"'])(?:ide|desktop)(?:$|[-_\s/\"'])", surface_val)
            or re.search(r"(?:^|[-_\s/\"'])(?:ide|desktop)(?:$|[-_\s/\"'])", client_val)
            or "antigravity-ide" in transcript_p
            or "antigravity-ide" in app_data_dir
        ):
            return

    settings_path = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")
    try:
        data: dict = {}
        loaded: dict = {}
        if os.path.isfile(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                raw_loaded = json.load(f)
                if not isinstance(raw_loaded, dict):
                    return
                loaded = raw_loaded
                data = dict(loaded)

        changed = False
        if "toolPermission" not in data:
            data["toolPermission"] = "always-proceed"
            changed = True
        if "artifactReviewPolicy" not in data:
            data["artifactReviewPolicy"] = "always-proceed"
            changed = True
        if "allowNonWorkspaceAccess" not in data:
            data["allowNonWorkspaceAccess"] = True
            changed = True

        if "autoApprove" not in data:
            data["autoApprove"] = {
                "all": True,
                "read": True,
                "edit": True,
                "write": True,
                "command": ["*"],
            }
            changed = True

        if "statusLine" not in data:
            statusline_bin = shutil.which("agy-statusline") or os.path.expanduser("~/.local/bin/agy-statusline")
            data["statusLine"] = {
                "type": "command",
                "command": f"python3 {statusline_bin}",
                "enabled": True,
            }
            changed = True

        # Check if root '/' is an active workspace
        is_root_active = False
        if payload:
            ws_paths = payload.get("workspacePaths", [])
            if isinstance(ws_paths, list) and any(str(w).strip() == "/" for w in ws_paths):
                is_root_active = True
        if not is_root_active and os.getcwd() == "/":
            is_root_active = True

        trusted = data.get("trustedWorkspaces")
        if not is_root_active and isinstance(trusted, list) and "/" in trusted:
            new_trusted = [w for w in trusted if w != "/"]
            if new_trusted != trusted:
                data["trustedWorkspaces"] = new_trusted
                changed = True

        if changed and data != loaded:
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            tmp_path = f"{settings_path}.tmp.{os.getpid()}"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
            os.replace(tmp_path, settings_path)
    except Exception:
        pass


@functools.lru_cache(maxsize=32)
def _inspect_transcript_compaction(transcript_p: str, transcript_size: int, invocation_num: int) -> tuple[int, int, bool, int]:
    """
    Inspects transcript.jsonl to find the LAST step where "type": "USER_INPUT" contains "<CONTEXT_SUMMARY>" in "content".
    Returns (bytes_since_compact, turns_since_compact, has_compact, last_compact_byte_offset).
    """
    if not transcript_p or not os.path.isfile(transcript_p):
        return (transcript_size, invocation_num, False, -1)

    last_compact_byte_offset = -1
    user_inputs_after = 0
    has_compact = False

    try:
        with open(transcript_p, "r", encoding="utf-8", errors="replace") as f:
            offset = 0
            for line in f:
                line_len = len(line.encode("utf-8"))
                if "<CONTEXT_SUMMARY>" in line:
                    try:
                        data = json.loads(line)
                        if data.get("type") == "USER_INPUT" and "<CONTEXT_SUMMARY>" in str(data.get("content", "")):
                            last_compact_byte_offset = offset + line_len
                            user_inputs_after = 0
                            has_compact = True
                    except Exception:
                        pass
                elif has_compact:
                    if '"USER_INPUT"' in line:
                        try:
                            data = json.loads(line)
                            if data.get("type") == "USER_INPUT":
                                user_inputs_after += 1
                        except Exception:
                            pass
                offset += line_len
    except Exception:
        return (transcript_size, invocation_num, False, -1)

    if has_compact and last_compact_byte_offset >= 0:
        bytes_since = max(0, transcript_size - last_compact_byte_offset)
        return (bytes_since, user_inputs_after, True, last_compact_byte_offset)
    return (transcript_size, invocation_num, False, -1)


def _check_context_health_alert(payload: dict, is_subagent: bool, invocation_num: int) -> str:
    if is_subagent:
        return ""

    conv_id = payload.get("conversationId", "")
    transcript_p = payload.get("transcriptPath", "")
    if not transcript_p or not os.path.isfile(transcript_p):
        if conv_id:
            for root in (
                "~/.gemini/antigravity-cli/brain",
                "~/.gemini/antigravity-ide/brain",
                "~/.gemini/antigravity/brain",
            ):
                cand = os.path.expanduser(f"{root}/{conv_id}/.system_generated/logs/transcript.jsonl")
                if os.path.isfile(cand):
                    transcript_p = cand
                    break
                cand2 = os.path.expanduser(f"{root}/{conv_id}/transcript.jsonl")
                if os.path.isfile(cand2):
                    transcript_p = cand2
                    break

    if not transcript_p or not os.path.isfile(transcript_p):
        return ""

    try:
        transcript_size = os.path.getsize(transcript_p)
    except OSError:
        transcript_size = 0

    bytes_since_compact, turns_since_compact, has_compact, compact_offset = _inspect_transcript_compaction(
        transcript_p, transcript_size, invocation_num
    )

    # If a <CONTEXT_SUMMARY> occurred within the last 5 USER_INPUT turns and bytes <= 500KB, return "" immediately
    if has_compact and (turns_since_compact < 5) and (bytes_since_compact <= 500_000):
        return ""

    if not conv_id and transcript_p:
        m = re.search(r"/brain/([a-f0-9\-]+)/", transcript_p)
        if m:
            conv_id = m.group(1)

    active_tokens = 0
    active_pct = 0.0
    has_live_usage = False
    live_state_path = getattr(sys.modules[__name__], "LIVE_STATE_PATH", os.path.expanduser("~/.cache/antigravity_live_state.json"))
    try:
        if os.path.isfile(live_state_path):
            mtime = os.path.getmtime(live_state_path)
            if time.time() - mtime <= 600:
                with open(live_state_path, "r", encoding="utf-8") as f:
                    live_data = json.load(f)
                live_conv_id = live_data.get("conversation_id")
                if live_conv_id and conv_id and live_conv_id == conv_id:
                    ctx_obj = live_data.get("context_window") or {}
                    curr = ctx_obj.get("current_usage")
                    if isinstance(curr, dict) and curr:
                        active_tokens = (curr.get("input_tokens") or 0) + (curr.get("cache_read_input_tokens") or 0)
                        ctx_limit = max(200_000, int(ctx_obj.get("context_window_size") or 1_048_576))
                        active_pct = (active_tokens / ctx_limit) * 100.0 if ctx_limit > 0 else 0.0
                        if active_tokens > 0:
                            has_live_usage = True
    except Exception:
        has_live_usage = False
        active_tokens = 0
        active_pct = 0.0

    if has_live_usage:
        is_saturated = (active_pct >= 55.0)
    else:
        is_saturated = (bytes_since_compact > 500_000) or (turns_since_compact >= 20)

    if not is_saturated:
        return ""

    # Remove stale alert files older than 3600s
    for stale in glob.glob("/tmp/agy_ctx_alert_*") + glob.glob("/tmp/.antigravity_ctx_alert_*"):
        try:
            if time.time() - os.path.getmtime(stale) > 3600:
                os.remove(stale)
        except Exception:
            pass

    key_src = conv_id or transcript_p or "default_session"
    cache_key = hashlib.sha256(f"ctx_alert:{key_src}".encode("utf-8")).hexdigest()[:16]
    state_file = os.path.join(tempfile.gettempdir(), f".antigravity_ctx_alert_{cache_key}.json")
    state: dict = {}
    if os.path.isfile(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}

    if has_compact and compact_offset != state.get("last_compact_offset", -1):
        state["last_compact_offset"] = compact_offset
        state["crossed_500k"] = False
        state["crossed_1m"] = False

    crossed_500k = state.get("crossed_500k", False)
    crossed_1m = state.get("crossed_1m", False)

    should_fire = False
    if has_live_usage:
        if active_pct >= 75.0 and not crossed_1m:
            should_fire = True
            state["crossed_1m"] = True
        elif active_pct >= 55.0 and not crossed_500k:
            should_fire = True
            state["crossed_500k"] = True
        elif turns_since_compact % 10 == 0:
            should_fire = True
    else:
        if (bytes_since_compact >= 1_000_000 or active_tokens >= 200_000) and not crossed_1m:
            should_fire = True
            state["crossed_1m"] = True
        elif (bytes_since_compact >= 500_000 or turns_since_compact >= 20 or active_tokens >= 120_000) and not crossed_500k:
            should_fire = True
            state["crossed_500k"] = True
        elif turns_since_compact % 10 == 0:
            should_fire = True

    if not should_fire:
        return ""

    state["last_alert_invocation"] = invocation_num
    try:
        tmp_s = f"{state_file}.tmp"
        with open(tmp_s, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp_s, state_file)
    except Exception:
        pass

    if has_live_usage:
        severity = "CRITICAL" if active_pct >= 75.0 else "DEGRADED"
        reason_str = f"context usage {active_pct:.1f}% >= 55%"
    else:
        severity = "CRITICAL" if (bytes_since_compact >= 1_000_000 or turns_since_compact >= 40 or active_tokens >= 200_000) else "DEGRADED"
        reason_str = "transcript > 500KB or turn >= 20"

    obs_file = os.path.expanduser(f"~/.cache/antigravity_observations/{conv_id}.md") if conv_id else ""
    obs_snippet = ""
    if obs_file and os.path.isfile(obs_file):
        try:
            with open(obs_file, "r", encoding="utf-8") as f:
                obs_text = f.read().strip()
            if obs_text:
                last_600 = obs_text[-600:].strip()
                obs_snippet = f"\n[Distilled Observation Prefix]: {last_600}"
        except Exception:
            pass

    return (
        f"[Context Health Alert: {severity} ({reason_str})] -> "
        "Automatically run context_health:compact_observations + context_health:commit_context_ledger when needed, "
        "delegate heavy multi-file work to subagents, and recommend /compact to the user at the end of the turn."
        f"{obs_snippet}"
    )


def _extract_prompt_keywords(prompt: str) -> list[str]:
    if not prompt:
        return []
    if "<USER_REQUEST>" in prompt:
        m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", prompt, re.DOTALL)
        if m:
            prompt = m.group(1)

    stopwords = {
        "about", "above", "across", "after", "again", "against", "all", "almost",
        "along", "already", "also", "always", "among", "and", "another", "any",
        "anyone", "anything", "anywhere", "are", "aren't", "around", "because",
        "been", "before", "behind", "being", "below", "between", "both", "cannot",
        "could", "couldn't", "describe", "detail", "did", "didn't", "does",
        "doesn't", "doing", "done", "down", "during", "each", "either", "else",
        "enough", "even", "ever", "every", "everyone", "everything", "everywhere",
        "file", "files", "find", "first", "five", "four", "from", "further", "give",
        "have", "haven't", "having", "here", "here's", "into", "just", "keep",
        "last", "like", "look", "make", "many", "more", "most", "mostly", "much",
        "must", "mustn't", "need", "next", "none", "only", "other", "others",
        "otherwise", "ought", "ours", "ourselves", "over", "please", "same",
        "should", "shouldn't", "show", "some", "someone", "something", "sometimes",
        "somewhere", "still", "such", "system", "take", "than", "that", "theirs",
        "them", "themselves", "then", "there", "there's", "these", "they", "they'd",
        "they'll", "they're", "they've", "this", "those", "through", "under",
        "until", "using", "very", "want", "what", "what's", "when", "when's",
        "where", "where's", "which", "while", "who", "who's", "whom", "will",
        "with", "within", "without", "won't", "work", "would", "wouldn't",
        "your", "yours", "yourself", "yourselves", "code", "task", "test",
        "true", "false", "none", "null", "token", "tokens", "session",
        "sessions", "question", "questions", "issue", "issues", "problem",
        "problems", "check", "why", "how"
    }

    raw_tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", prompt)
    tokens: list[str] = []
    seen: set[str] = set()
    for tok in raw_tokens:
        tok_lower = tok.lower()
        if tok_lower not in stopwords and tok_lower not in seen:
            seen.add(tok_lower)
            tokens.append(tok)
    return tokens


def _get_codegraph_seed(prompt: str, workspace: str) -> str:
    tokens = _extract_prompt_keywords(prompt)
    if not tokens:
        return ""

    db_path = os.path.expanduser("~/.local/share/codex/codegraph_index.sqlite")
    if not os.path.isfile(db_path):
        return ""

    conn = None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=0.5)
        conn.execute("PRAGMA busy_timeout=500;")
        cur = conn.cursor()
        cols = [r[1] for r in cur.execute("PRAGMA table_info(symbols);").fetchall()]
        has_workspace = "workspace" in cols
        has_exported = "exported" in cols
        has_pagerank = "pagerank" in cols

        matched_symbols: list[dict] = []
        seen_keys: set[tuple[str, str, int]] = set()
        heading_rank_expr = "CASE WHEN LOWER(kind) = 'heading' THEN 1 ELSE 0 END ASC"

        def _non_heading_count(items: list[dict]) -> int:
            return sum(1 for item in items if str(item.get("kind", "")).lower() != "heading")

        for tok in tokens[:8]:
            if has_workspace and has_exported:
                order_clause = (
                    f"ORDER BY {heading_rank_expr}, pagerank DESC, exported DESC, line ASC LIMIT 5;"
                    if has_pagerank
                    else f"ORDER BY {heading_rank_expr}, exported DESC, line ASC LIMIT 5;"
                )
                select_clause = "SELECT name, kind, path, line, end_line, exported, pagerank FROM symbols " if has_pagerank else "SELECT name, kind, path, line, end_line, exported, 0 FROM symbols "
                query_exact = (
                    f"{select_clause}"
                    "WHERE (workspace = ? OR ? = '') AND LOWER(name) = LOWER(?) "
                    f"{order_clause}"
                )
                params_exact = (workspace, workspace, tok)
            elif has_workspace:
                query_exact = (
                    "SELECT name, kind, path, line, end_line, 0, 0 FROM symbols "
                    "WHERE (workspace = ? OR ? = '') AND LOWER(name) = LOWER(?) "
                    f"ORDER BY {heading_rank_expr}, line ASC LIMIT 5;"
                )
                params_exact = (workspace, workspace, tok)
            elif has_exported:
                order_clause = (
                    f"ORDER BY {heading_rank_expr}, pagerank DESC, exported DESC, line ASC LIMIT 5;"
                    if has_pagerank
                    else f"ORDER BY {heading_rank_expr}, exported DESC, line ASC LIMIT 5;"
                )
                select_clause = "SELECT name, kind, path, line, end_line, exported, pagerank FROM symbols " if has_pagerank else "SELECT name, kind, path, line, end_line, exported, 0 FROM symbols "
                query_exact = (
                    f"{select_clause}"
                    "WHERE LOWER(name) = LOWER(?) "
                    f"{order_clause}"
                )
                params_exact = (tok,)
            else:
                query_exact = (
                    "SELECT name, kind, path, line, end_line, 0, 0 FROM symbols "
                    f"WHERE LOWER(name) = LOWER(?) ORDER BY {heading_rank_expr}, line ASC LIMIT 5;"
                )
                params_exact = (tok,)

            try:
                for row in cur.execute(query_exact, params_exact).fetchall():
                    key = (row[0], row[2], int(row[3]))
                    if key not in seen_keys:
                        seen_keys.add(key)
                        matched_symbols.append({
                            "name": row[0],
                            "kind": row[1],
                            "path": row[2],
                            "line": int(row[3]),
                            "end_line": int(row[4]),
                            "exported": int(row[5]),
                            "pagerank": float(row[6]) if len(row) > 6 and row[6] is not None else 0.0,
                            "exact": 1,
                        })
            except Exception:
                pass
            if _non_heading_count(matched_symbols) >= 5:
                break

        if _non_heading_count(matched_symbols) < 5:
            for tok in tokens[:5]:
                like_pat = f"%{tok}%"
                if has_workspace and has_exported:
                    order_clause = (
                        f"ORDER BY {heading_rank_expr}, pagerank DESC, exported DESC, line ASC LIMIT 5;"
                        if has_pagerank
                        else f"ORDER BY {heading_rank_expr}, exported DESC, line ASC LIMIT 5;"
                    )
                    select_clause = "SELECT name, kind, path, line, end_line, exported, pagerank FROM symbols " if has_pagerank else "SELECT name, kind, path, line, end_line, exported, 0 FROM symbols "
                    query_like = (
                        f"{select_clause}"
                        "WHERE (workspace = ? OR ? = '') AND name LIKE ? "
                        f"{order_clause}"
                    )
                    params_like = (workspace, workspace, like_pat)
                elif has_workspace:
                    query_like = (
                        "SELECT name, kind, path, line, end_line, 0, 0 FROM symbols "
                        "WHERE (workspace = ? OR ? = '') AND name LIKE ? "
                        f"ORDER BY {heading_rank_expr}, line ASC LIMIT 5;"
                    )
                    params_like = (workspace, workspace, like_pat)
                elif has_exported:
                    order_clause = (
                        f"ORDER BY {heading_rank_expr}, pagerank DESC, exported DESC, line ASC LIMIT 5;"
                        if has_pagerank
                        else f"ORDER BY {heading_rank_expr}, exported DESC, line ASC LIMIT 5;"
                    )
                    select_clause = "SELECT name, kind, path, line, end_line, exported, pagerank FROM symbols " if has_pagerank else "SELECT name, kind, path, line, end_line, exported, 0 FROM symbols "
                    query_like = (
                        f"{select_clause}"
                        "WHERE name LIKE ? "
                        f"{order_clause}"
                    )
                    params_like = (like_pat,)
                else:
                    query_like = (
                        "SELECT name, kind, path, line, end_line, 0, 0 FROM symbols "
                        f"WHERE name LIKE ? ORDER BY {heading_rank_expr}, line ASC LIMIT 5;"
                    )
                    params_like = (like_pat,)

                try:
                    for row in cur.execute(query_like, params_like).fetchall():
                        key = (row[0], row[2], int(row[3]))
                        if key not in seen_keys:
                            seen_keys.add(key)
                            matched_symbols.append({
                                "name": row[0],
                                "kind": row[1],
                                "path": row[2],
                                "line": int(row[3]),
                                "end_line": int(row[4]),
                                "exported": int(row[5]),
                                "pagerank": float(row[6]) if len(row) > 6 and row[6] is not None else 0.0,
                                "exact": 0,
                            })
                except Exception:
                    pass
                if _non_heading_count(matched_symbols) >= 5:
                    break

        if not matched_symbols:
            return ""

        matched_symbols.sort(
            key=lambda s: (
                1 if str(s.get("kind", "")).lower() == "heading" else 0,
                -s["exact"],
                -s.get("pagerank", 0.0),
                -s.get("exported", 0),
                s["line"],
                str(s["name"]),
            )
        )
        top5 = matched_symbols[:5]

        entries: list[str] = []
        for s in top5:
            p = s["path"]
            if workspace and os.path.isabs(p) and p.startswith(workspace):
                try:
                    p = os.path.relpath(p, workspace)
                except Exception:
                    pass
            entries.append(f"{s['name']} ({s['kind']} @ {p}:{s['line']}-{s['end_line']})")

        return f"Target Symbols (Agentless RepoMap): {', '.join(entries)}"
    except Exception:
        return ""
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def _classify_harmony_task_mode(prompt_text: str) -> str:
    """Classifies task mode into strict_security vs balanced_velocity based on keywords (CP-1)."""
    if prompt_text and re.search(
        r"\b(?:"
        r"(?:auth|access|refresh|api|jwt|csrf|bearer|oauth|id|security|secret)[\s_-]*tokens?"
        r"|auth|security|secret|password|credential|migration|schema|permission|cve|vulnerability|rm|delete|production"
        r")\b",
        prompt_text,
        re.IGNORECASE,
    ):
        return "strict_security"
    return "balanced_velocity"


def _compose_harmony_harness_overlay(
    slug: str,
    prompt_text: str = "",
    env_overlays_dir: str | None = None,
    db_path: str | None = None,
) -> str:
    """Turn-1 Dynamic Composition H_gen ⊕ H_env under task mode (CP-1, CP-2, CP-3)."""
    if not slug or slug in ("global", "default"):
        return ""

    mode = _classify_harmony_task_mode(prompt_text)

    # 1. Inspect factorized environment overlay file
    eff_overlays_dir = (
        env_overlays_dir
        if env_overlays_dir
        else os.path.expanduser("~/.gemini/antigravity/skillbank/env_overlays")
    )
    overlay_file = Path(eff_overlays_dir) / f"{slug}.md"
    bullet_snippet = ""
    if overlay_file.is_file():
        try:
            lines = overlay_file.read_text(encoding="utf-8").splitlines()
            bullets = [
                line.strip().lstrip("-* ").strip()
                for line in lines
                if line.strip().startswith(("-", "*"))
            ]
            if bullets:
                bullet_snippet = "; ".join(bullets[:2])
                if len(bullet_snippet) > 160:
                    bullet_snippet = bullet_snippet[:157] + "..."
        except Exception:
            pass

    # 2. Query SQLite Pareto Frontier Profile
    eff_db = (
        db_path
        if db_path
        else os.path.expanduser("~/.local/share/codex/projects/registry.sqlite")
    )
    score_snippet = ""
    if os.path.isfile(eff_db):
        try:
            conn = sqlite3.connect(f"file:{eff_db}?mode=ro", uri=True, timeout=1.0)
            try:
                cur = conn.cursor()
                order_clause = (
                    "(CASE WHEN slug = ? THEN 0 ELSE 1 END), sec_score DESC, func_score DESC, token_score DESC"
                    if mode == "strict_security"
                    else "(CASE WHEN slug = ? THEN 0 ELSE 1 END), func_score DESC, token_score DESC, sec_score DESC"
                )
                row = cur.execute(
                    f"""
                    SELECT func_score, sec_score, token_score
                    FROM harness_pareto_archive
                    WHERE (slug = ? OR slug = 'global') AND is_pareto_front = 1
                    ORDER BY {order_clause}
                    LIMIT 1;
                    """,
                    (slug, slug),
                ).fetchone()
                if row:
                    score_snippet = f"Pareto ({row[0]:.2f}/{row[1]:.2f}/{row[2]:.2f})"
            finally:
                conn.close()
        except Exception:
            pass

    if not bullet_snippet and not score_snippet:
        return ""

    details = []
    if score_snippet:
        details.append(score_snippet)
    if bullet_snippet:
        details.append(bullet_snippet)
    detail_str = " | ".join(details)

    summary = f"- Harmony Harness (H_gen ⊕ H_env [{mode}]): {detail_str}"
    if len(summary) > 220:
        summary = summary[:217] + "..."
    return summary


def _get_active_behavioral_antipatterns(
    conv_id: str = "",
    registry_db_path: str | None = None,
    consume_feedback: bool = True,
    slug: str = "",
) -> list[str]:
    antipatterns: list[str] = []
    try:
        if conv_id:
            diag_file = os.path.join(tempfile.gettempdir(), f".antigravity_structured_feedback_{conv_id}.json")
            if os.path.isfile(diag_file):
                try:
                    with open(diag_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        ts = float(data.get("timestamp") or 0.0)
                        if ts > 0 and (time.time() - ts) > 180:
                            try:
                                os.unlink(diag_file)
                            except OSError:
                                pass
                            data = None

                        if data is not None:
                            lbl = str(data.get("failure_label") or data.get("label") or "").strip()
                            file_p = str(data.get("file") or data.get("path") or "").strip()
                            line_no = data.get("line") or data.get("line_number")
                            msg = str(data.get("message") or data.get("reason") or "").strip()
                            loc_part = f" at {file_p}:{line_no}" if (file_p and line_no) else (f" in {file_p}" if file_p else "")
                            tag = f"[{lbl}{loc_part}]" if (lbl or loc_part) else ""
                            msg_part = f": {msg}" if msg else ""
                            if tag or msg_part:
                                antipatterns.append(f"Recent Tool Failure {tag}{msg_part}".strip())

                            if consume_feedback:
                                try:
                                    os.unlink(diag_file)
                                except OSError:
                                    pass
                except Exception:
                    pass

        if registry_db_path:
            reg_db = registry_db_path
        else:
            codex_db = os.path.expanduser("~/.local/share/codex/projects/registry.sqlite")
            reg_db = codex_db if os.path.isfile(codex_db) else os.path.expanduser("~/.gemini/antigravity/skillbank/registry.sqlite")
        if os.path.isfile(reg_db):
            conn = None
            try:
                conn = sqlite3.connect(f"file:{reg_db}?mode=ro", uri=True, timeout=0.5)
                conn.execute("PRAGMA busy_timeout=500;")
                cur = conn.cursor()
                cols: set[str] = set()
                try:
                    cols = {row[1] for row in cur.execute("PRAGMA table_info(harness_failures);").fetchall()}
                except Exception:
                    cols = set()

                scope_clauses: list[str] = []
                scope_params: list[object] = []
                if slug and "slug" in cols:
                    scope_clauses.append("(slug = ? OR slug = 'global')")
                    scope_params.append(slug)
                if "created_at" in cols:
                    scope_clauses.append(
                        "(created_at IS NULL OR created_at = '' OR datetime(created_at) >= datetime('now', '-7 days'))"
                    )
                extra_filter_sql = (" AND " + " AND ".join(scope_clauses)) if scope_clauses else ""

                if conv_id and cols:
                    try:
                        res_clause = " AND (resolved_at IS NULL OR resolved_at = '')" if "resolved_at" in cols else ""
                        if "vertex" in cols:
                            q = f"""
                                SELECT COUNT(*)
                                FROM harness_failures
                                WHERE conv_id = ?
                                  AND (vertex = 'tool_guidance' OR failure_type IN ('slice_loop_breaker', 'flood_guard', 'slice_cap_exceeded', 'tool_guidance'))
                                  {res_clause}{extra_filter_sql};
                            """
                            tg_count = cur.execute(q, (conv_id, *scope_params)).fetchone()[0]
                        elif "failure_type" in cols:
                            q = f"""
                                SELECT COUNT(*)
                                FROM harness_failures
                                WHERE conv_id = ?
                                  AND failure_type IN ('slice_loop_breaker', 'flood_guard', 'slice_cap_exceeded', 'tool_guidance')
                                  {res_clause}{extra_filter_sql};
                            """
                            tg_count = cur.execute(q, (conv_id, *scope_params)).fetchone()[0]
                        else:
                            tg_count = 0
                        if tg_count >= 2:
                            antipatterns.append("DOM Micro-Tool Hint: Repeated tool friction detected; use codegraph:extract_symbols or synthesize a helper script in .antigravity/task_harness/scripts/")
                    except Exception:
                        pass
                if cols:
                    try:
                        where_parts: list[str] = []
                        if "resolved_at" in cols:
                            where_parts.append("(resolved_at IS NULL OR resolved_at = '')")
                        where_parts.extend(scope_clauses)
                        where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
                        order_sql = "cnt DESC, id DESC" if "id" in cols else "cnt DESC"
                        rows = cur.execute(
                            f"""
                            SELECT failure_type, reason, COUNT(*) as cnt
                            FROM harness_failures
                            {where_sql}
                            GROUP BY failure_type, reason
                            ORDER BY {order_sql}
                            LIMIT 3;
                            """,
                            tuple(scope_params),
                        ).fetchall()
                        for r in rows:
                            ftype = str(r[0] or "unknown").strip()
                            reason = str(r[1] or "").strip()
                            cnt = r[2]
                            snippet = f"{ftype} (count={cnt})"
                            if reason:
                                snippet += f": {reason[:60]}"
                            antipatterns.append(f"Recurring Failure: {snippet}")
                    except Exception:
                        pass

                if len(antipatterns) < 2:
                    try:
                        sr_cols = {row[1] for row in cur.execute("PRAGMA table_info(settings_reviews);").fetchall()}
                        if sr_cols:
                            sr_where: list[str] = []
                            sr_params: list[object] = []
                            if "resolved_at" in sr_cols:
                                sr_where.append("(resolved_at IS NULL OR resolved_at = '')")
                            if slug and "slug" in sr_cols:
                                sr_where.append("(slug = ? OR slug = 'global')")
                                sr_params.append(slug)
                            if "created_at" in sr_cols:
                                sr_where.append(
                                    "(created_at IS NULL OR created_at = '' OR datetime(created_at) >= datetime('now', '-7 days'))"
                                )
                            sr_where_sql = f"WHERE {' AND '.join(sr_where)}" if sr_where else ""
                            sr_order = "event_count DESC, id DESC" if "id" in sr_cols else "event_count DESC"
                            rows = cur.execute(
                                f"""
                                SELECT reason, event_count
                                FROM settings_reviews
                                {sr_where_sql}
                                ORDER BY {sr_order}
                                LIMIT 3;
                                """,
                                tuple(sr_params),
                            ).fetchall()
                            for r in rows:
                                reason = str(r[0] or "").strip()
                                cnt = r[1] or 1
                                if reason:
                                    antipatterns.append(f"Pending Review (count={cnt}): {reason[:70]}")
                    except Exception:
                        pass
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
    except Exception:
        return []

    return antipatterns[:4] if any("DOM Micro-Tool Hint" in a for a in antipatterns) else antipatterns[:3]


def _build_turn1_grounding(slug: str, workspace: str, payload: dict) -> str:
    _auto_ensure_verification_gates(workspace)
    raw_prompt = (
        payload.get("lastUserInput")
        or payload.get("userPrompt")
        or payload.get("prompt")
        or ""
    )
    prompt = _strip_user_request_tags(str(raw_prompt)) or _get_latest_user_prompt(payload)
    memories, entities = _get_dynamic_seeds(slug, prompt)
    has_gates = os.path.isfile(os.path.join(workspace, "scripts/verification/verify-oracle.sh"))
    sot_files = _find_existing_sot_docs(workspace)
    sot_ref = f" (refer to {sot_files[0]})" if sot_files else ""
    mem_str = ", ".join(memories) if memories else f"none{sot_ref}"
    ent_str = ", ".join(entities) if entities else "none"

    codegraph_seed = _get_codegraph_seed(prompt, workspace)

    overlay_summary = ""
    overlay_dir = os.path.join(workspace, ".antigravity", "task_harness")
    if os.path.isdir(overlay_dir):
        try:
            active_files = [f for f in os.listdir(overlay_dir) if not f.startswith(".")]
            if active_files:
                summary = f"- Active Task Harness Overlay (.antigravity/task_harness/): {len(active_files)} active file(s) ({', '.join(sorted(active_files)[:3])})."
                if len(summary) > 200:
                    summary = summary[:197] + "..."
                overlay_summary = summary
        except Exception:
            pass

    harmony_summary = _compose_harmony_harness_overlay(slug, prompt)

    conv_id = str(payload.get("conversationId") or "").strip()
    if not conv_id:
        transcript_p = str(payload.get("transcriptPath") or "").strip()
        if transcript_p:
            m = re.search(r"/brain/([a-f0-9\-]+)/", transcript_p)
            if m:
                conv_id = m.group(1)

    session_start_emitted = _has_session_start_been_emitted(conv_id) if conv_id else False
    if session_start_emitted:
        mem_str = ", ".join(memories) if memories else "none"

    antipatterns = _get_active_behavioral_antipatterns(conv_id, slug=slug)
    anti_line = ""
    if antipatterns:
        anti_summary = "; ".join(antipatterns)
        if len(anti_summary) > 200:
            anti_summary = anti_summary[:197] + "..."
        anti_line = f"- Behavioral Anti-Patterns: {anti_summary}"

    if sot_files:
        sot_cite = ", ".join(sot_files[:2])
        query_protocol = f"- Query Protocol: Prefer project-local SOT docs ({sot_cite}) and targeted ripgrep before broad file scanning."
    else:
        query_protocol = "- Query Protocol: Prefer targeted ripgrep before broad file scanning."

    if session_start_emitted:
        lines = [
            "[Active Knowledge Grounding - Turn-1 Dynamic Overlay]",
            f"- Dynamic Memory Seeds: {mem_str}",
            f"- Key Graph Entities: {ent_str}",
        ]
    else:
        lines = [
            f"[Active Knowledge Grounding - {slug}]",
            f"- Dynamic Memory Seeds: {mem_str}",
            f"- Key Graph Entities: {ent_str}",
        ]
    if has_gates:
        lines.append("- SOL Verification Gates: Active (scripts/verification/verify-oracle.sh & test-3-round-loop.sh)")
    if codegraph_seed:
        lines.append(f"- {codegraph_seed}")
    if overlay_summary:
        lines.append(overlay_summary)
    if harmony_summary:
        lines.append(harmony_summary)
    if anti_line:
        lines.append(anti_line)
    if not session_start_emitted:
        lines.append(query_protocol)
    return "\n".join(lines)


def _check_and_consume_stale_reads(payload: dict) -> str:
    conv_id = str(payload.get("conversationId") or "").strip()
    if not conv_id:
        transcript_p = str(payload.get("transcriptPath") or "").strip()
        if transcript_p:
            m = re.search(r"/brain/([a-f0-9\-]+)/", transcript_p)
            if m:
                conv_id = m.group(1)
    if not conv_id:
        return ""

    tmp_dir = Path(tempfile.gettempdir())
    tracker_file = tmp_dir / f".antigravity_superseded_{conv_id}.json"
    if not tracker_file.is_file():
        return ""

    try:
        data = json.loads(tracker_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return ""
    except Exception:
        return ""

    now = time.time()
    stale_items: list[str] = []
    seen_basenames: set[str] = set()
    needs_update = False

    for file_path, info in data.items():
        if not isinstance(info, dict):
            continue
        mutated_at = info.get("mutated_at", 0)
        delivered = info.get("delivered", False)
        if not delivered and (now - mutated_at <= 600):
            bname = os.path.basename(file_path)
            lines = info.get("lines", 0)
            if bname not in seen_basenames:
                seen_basenames.add(bname)
                stale_items.append(f"{bname} ({lines} lines now)")
            info["delivered"] = True
            needs_update = True

    if needs_update:
        try:
            tmp_f = tracker_file.with_suffix(".tmp")
            tmp_f.write_text(json.dumps(data, indent=2), encoding="utf-8")
            tmp_f.replace(tracker_file)
        except Exception:
            pass

    if stale_items:
        items_str = ", ".join(stale_items)
        return (
            f"[Stale-Read Tombstone]: Earlier read_file (CLI) / view_file (IDE) outputs for [{items_str}] "
            "are superseded by recent edits—rely on latest edit state, not earlier transcript dumps."
        )
    return ""


def _check_post_compaction_recovery(payload: dict) -> str:
    """ClaudeKit LOSS-02: Surfaces a compact recovery anchor if the session was compacted
    and a fresh (<3600s) session state snapshot exists.
    """
    conv_id = payload.get("conversationId", "")
    transcript_p = payload.get("transcriptPath", "")
    if not transcript_p or not os.path.isfile(transcript_p):
        if conv_id:
            for root in (
                "~/.gemini/antigravity-cli/brain",
                "~/.gemini/antigravity-ide/brain",
                "~/.gemini/antigravity/brain",
            ):
                cand = os.path.expanduser(f"{root}/{conv_id}/.system_generated/logs/transcript.jsonl")
                if os.path.isfile(cand):
                    transcript_p = cand
                    break
                cand2 = os.path.expanduser(f"{root}/{conv_id}/transcript.jsonl")
                if os.path.isfile(cand2):
                    transcript_p = cand2
                    break

    if not conv_id and transcript_p:
        m = re.search(r"/brain/([a-f0-9\-]+)/", transcript_p)
        if m:
            conv_id = m.group(1)

    if not conv_id:
        return ""

    snapshot_file = os.path.expanduser(f"~/.cache/antigravity_session_states/{conv_id}.md")
    if not os.path.isfile(snapshot_file):
        return ""

    try:
        if (time.time() - os.path.getmtime(snapshot_file)) >= 3600:
            return ""
    except Exception:
        return ""

    # Check if the session was compacted
    is_compacted = False
    source = payload.get("source")
    if source == "compact":
        is_compacted = True
    elif transcript_p and os.path.isfile(transcript_p):
        try:
            fsize = os.path.getsize(transcript_p)
            invocation_num = payload.get("invocationNum", 1)
            _, turns_since_compact, has_compact, _ = _inspect_transcript_compaction(
                transcript_p, fsize, invocation_num
            )
            if has_compact and turns_since_compact <= 1:
                is_compacted = True
        except Exception:
            pass

    if not is_compacted:
        return ""

    # Prevent surfacing multiple times for the same compaction turn
    surfaced_flag = os.path.join(tempfile.gettempdir(), f"antigravity_recovery_surfaced_{conv_id}.flag")
    if os.path.isfile(surfaced_flag):
        return ""

    try:
        Path(surfaced_flag).touch()
    except Exception:
        pass

    try:
        with open(snapshot_file, "r", encoding="utf-8") as f:
            snapshot_content = f.read().strip()
        if snapshot_content:
            return (
                "[Post-Compaction Recovery Anchor (ClaudeKit)]\n"
                "Context was compacted. Below is your saved progress snapshot from before compaction:\n\n"
                f"{snapshot_content}\n\n"
                "Resume from where you left off. Re-read active plan files and do NOT redo completed work."
            )
    except Exception:
        pass

    return ""


def _check_and_consume_auto_heal_alert() -> str:
    """Checks for Level-3 Autonomous Sleep-Time Self-Heal alert flag and consumes it."""
    if "unittest" in sys.modules and not os.environ.get("ANTIGRAVITY_TEST_HEAL_ALERT"):
        return ""
    flag_path = os.path.expanduser("~/.gemini/last_harness_evolution_alert.flag")
    if not os.path.isfile(flag_path):
        return ""
    try:
        with open(flag_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        try:
            os.unlink(flag_path)
        except OSError:
            pass
        if content:
            truncated = content[:200]
            return f"[Autonomous Harness Self-Heal Notice]\n{truncated}"
    except Exception:
        pass
    return ""


def _reap_stale_tmp_artifacts(max_age_sec: int = 86400) -> int:
    reaped = 0
    now = time.time()
    tmp_dir = tempfile.gettempdir()
    try:
        patterns = [
            os.path.join(tmp_dir, ".antigravity_*"),
            os.path.join(tmp_dir, "agy_*"),
        ]
        for pat in patterns:
            for p in glob.glob(pat):
                try:
                    if p.endswith(".lock"):
                        continue
                    st = os.stat(p)
                    if (now - st.st_mtime) > max_age_sec:
                        if os.path.isfile(p):
                            os.remove(p)
                            reaped += 1
                        elif os.path.isdir(p):
                            shutil.rmtree(p, ignore_errors=True)
                            reaped += 1
                except Exception:
                    continue
    except Exception:
        pass
    try:
        states_dir = os.environ.get("ANTIGRAVITY_SESSION_STATES_DIR") or os.path.expanduser(
            "~/.cache/antigravity_session_states"
        )
        if states_dir and os.path.isdir(states_dir):
            for entry in os.scandir(states_dir):
                try:
                    if entry.name.endswith(".lock") or entry.name.startswith(".lock"):
                        continue
                    if not entry.is_file(follow_symlinks=False):
                        continue
                    st = entry.stat(follow_symlinks=False)
                    if (now - st.st_mtime) > max_age_sec:
                        os.remove(entry.path)
                        reaped += 1
                except Exception:
                    continue
    except Exception:
        pass
    return reaped


def _auto_disable_browseros_mcp(payload: dict) -> None:
    """Ensures browseros-neo is popped from mcpServers on session start unless explicitly requested (zero-write otherwise)."""
    try:
        user_prompt = _get_latest_user_prompt(payload).lower()
        if any(term in user_prompt for term in ("browseros", "use neo", "browserclaw", "open neo")):
            return

        mcp_cfg_path = os.path.expanduser("~/.gemini/config/mcp_config.json")
        if not os.path.isfile(mcp_cfg_path):
            return

        with open(mcp_cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        mcp_servers = cfg.get("mcpServers", {})
        if not isinstance(mcp_servers, dict) or "browseros-neo" not in mcp_servers:
            return

        mcp_servers.pop("browseros-neo", None)
        cfg["mcpServers"] = mcp_servers

        tmp_path = f"{mcp_cfg_path}.tmp.{os.getpid()}"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        os.replace(tmp_path, mcp_cfg_path)
    except Exception:
        pass


def _session_states_cache_dir() -> str:
    override_dir = os.environ.get("ANTIGRAVITY_SESSION_STATES_DIR")
    return override_dir or os.path.expanduser("~/.cache/antigravity_session_states")


def _has_session_start_been_emitted(conv_id: str) -> bool:
    if not conv_id:
        return False
    sanitized = re.sub(r"[^a-zA-Z0-9_\-]", "_", conv_id)
    marker = os.path.join(_session_states_cache_dir(), f"{sanitized}.session_start_emitted")
    if os.path.isfile(marker):
        try:
            mtime = os.path.getmtime(marker)
            if (time.time() - mtime) < 12 * 3600:
                return True
            try:
                os.unlink(marker)
            except OSError:
                pass
        except Exception:
            pass
    return False


def _mark_session_start_emitted(conv_id: str) -> str | None:
    if not conv_id:
        return None
    sanitized = re.sub(r"[^a-zA-Z0-9_\-]", "_", conv_id)
    cache_dir = _session_states_cache_dir()
    try:
        os.makedirs(cache_dir, exist_ok=True)
        marker = os.path.join(cache_dir, f"{sanitized}.session_start_emitted")
        with open(marker, "w", encoding="utf-8") as f:
            f.write(str(time.time()))
        return marker
    except Exception:
        return None


def _scan_workspace_untrusted_customizations(workspace: str) -> list[str]:
    if not workspace or not os.path.isdir(workspace):
        return []
    hazards: list[str] = []
    for rel in (
        ".agents/hooks.json",
        ".agent/hooks.json",
        "_agents/hooks.json",
        "_agent/hooks.json",
    ):
        cand = os.path.join(workspace, rel)
        if os.path.lexists(cand):
            hazards.append(rel)
    plugins_dir = os.path.join(workspace, ".agents", "plugins")
    if os.path.isdir(plugins_dir):
        try:
            if any(not f.startswith(".") for f in os.listdir(plugins_dir)):
                hazards.append(".agents/plugins/")
        except Exception:
            pass
    return hazards


def _compose_static_prefix_pin(
    slug: str,
    role: str = "root",
    sot_docs: list[str] | None = None,
) -> tuple[str, str]:
    norm_slug = str(slug or "default").strip() or "default"
    norm_role = str(role or "root").strip().lower() or "root"
    docs_sorted = sorted(str(d).strip() for d in (sot_docs or []) if d and str(d).strip())
    canonical = json.dumps(
        {"slug": norm_slug, "role": norm_role, "sot_docs": docs_sorted},
        sort_keys=True,
        separators=(",", ":"),
    )
    prefix_pin = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:8]
    sot_str = ", ".join(docs_sorted[:3]) if docs_sorted else "none"
    static_header = (
        f"[Session Grounding Anchor] ({norm_slug})\n"
        f"- Prefix-Pin: {prefix_pin} | Role: {norm_role}\n"
        f"- Project Slug: {norm_slug} | Workspace SOT: {sot_str}"
    )
    return prefix_pin, static_header


def _build_session_start_anchor(slug: str, workspace: str, payload: dict | None = None) -> str:
    sot_files = _find_existing_sot_docs(workspace)
    role = (
        str((payload or {}).get("subagentRole") or (payload or {}).get("role") or "root").strip()
        or "root"
    )
    _, static_header = _compose_static_prefix_pin(slug, role=role, sot_docs=sot_files)
    memories = _get_cue_matched_memory_keys(slug, "", limit=3)
    mem_str = ", ".join(memories[:3]) if memories else "none"
    hazards = _scan_workspace_untrusted_customizations(workspace)
    lines = [
        static_header,
        f"- Memory Keys: {mem_str}",
    ]
    if hazards:
        lines.append(
            f"- [SECURITY ALERT] Untrusted Priority #1 customization in workspace: {', '.join(hazards)}"
        )
    anchor = "\n".join(lines)
    if len(anchor) > 600:
        anchor = anchor[:597].rstrip() + "..."
    return anchor


def _maybe_run_herdr_resume_fallback(conv_id: str, payload: dict) -> bool:
    if os.environ.get("HERDR_ENV") != "1":
        return False
    if conv_id and _has_session_start_been_emitted(conv_id):
        return False
    herdr_script = os.environ.get(
        "ANTIGRAVITY_HERDR_SCRIPT",
        os.path.expanduser("~/.gemini/config/hooks/herdr-agent-state.sh"),
    )
    if not os.path.isfile(herdr_script):
        local_cand = os.path.join(os.path.dirname(os.path.abspath(__file__)), "herdr-agent-state.sh")
        if os.path.isfile(local_cand):
            herdr_script = local_cand
    try:
        subprocess.run(
            ["bash", herdr_script, "session"],
            input=json.dumps(payload),
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=False,
        )
        return True
    except Exception:
        return False


def _has_turn1_been_emitted(conv_id: str) -> bool:
    if not conv_id:
        return False
    is_test_env = "unittest" in sys.modules or "pytest" in sys.modules
    override_dir = os.environ.get("ANTIGRAVITY_SESSION_STATES_DIR")
    if is_test_env and not override_dir:
        return False

    sanitized = re.sub(r"[^a-zA-Z0-9_\-]", "_", conv_id)
    cache_dir = override_dir or os.path.expanduser("~/.cache/antigravity_session_states")
    marker = os.path.join(cache_dir, f"{sanitized}.turn1_emitted")
    if os.path.isfile(marker):
        try:
            mtime = os.path.getmtime(marker)
            if (time.time() - mtime) < 12 * 3600:
                return True
            try:
                os.unlink(marker)
            except OSError:
                pass
        except Exception:
            pass
    return False


def _mark_turn1_emitted(conv_id: str) -> None:
    if not conv_id:
        return
    is_test_env = "unittest" in sys.modules or "pytest" in sys.modules
    override_dir = os.environ.get("ANTIGRAVITY_SESSION_STATES_DIR")
    if is_test_env and not override_dir:
        return

    sanitized = re.sub(r"[^a-zA-Z0-9_\-]", "_", conv_id)
    cache_dir = override_dir or os.path.expanduser("~/.cache/antigravity_session_states")
    try:
        os.makedirs(cache_dir, exist_ok=True)
        marker = os.path.join(cache_dir, f"{sanitized}.turn1_emitted")
        with open(marker, "w", encoding="utf-8") as f:
            f.write(str(time.time()))
    except Exception:
        pass


def _format_and_cap_alerts(
    alert_list: list[str],
    max_chars: int = 1500,
    trunc_marker: str = "…(truncated)",
) -> str:
    valid_alerts = [a.strip() for a in alert_list if a and a.strip()]
    if not valid_alerts:
        return ""
    combined = "\n\n".join(valid_alerts)
    if len(combined) <= max_chars:
        return combined
    budget = max_chars - len(trunc_marker)
    if budget <= 0:
        return trunc_marker[:max_chars]
    return combined[:budget].rstrip() + trunc_marker


def _run_session_start(payload: dict) -> None:
    conv_id = _resolve_conv_id(payload)
    if conv_id and not payload.get("conversationId"):
        payload = dict(payload, conversationId=conv_id)

    if _is_subagent_conversation(payload):
        print(json.dumps({"injectSteps": []}))
        return

    _ensure_cli_statusline_and_yolo_settings(payload)
    _reap_stale_tmp_artifacts(86400)
    _auto_disable_browseros_mcp(payload)

    ws_paths = payload.get("workspacePaths", [])
    workspace = ws_paths[0] if (ws_paths and isinstance(ws_paths, list)) else os.getcwd()
    slug = _resolve_project_slug(workspace)
    anchor = _build_session_start_anchor(slug, workspace, payload)
    if conv_id:
        _mark_session_start_emitted(conv_id)
    print(json.dumps({"injectSteps": [{"systemMessage": {"systemMessage": anchor}}]}))


def main() -> None:
    try:
        is_session_start = "--session-start" in sys.argv
        raw_input = sys.stdin.read()
        if is_session_start:
            payload = json.loads(raw_input) if raw_input.strip() else {}
            _run_session_start(payload)
            return

        if not raw_input.strip():
            _ensure_cli_statusline_and_yolo_settings()
            print(json.dumps({"injectSteps": []}))
            return

        payload = json.loads(raw_input)
        raw_inv = payload.get("invocationNum", 1)
        raw_inv_is_zero = (raw_inv == 0 and not isinstance(raw_inv, bool)) or (
            isinstance(raw_inv, str) and raw_inv.strip() == "0"
        )
        try:
            invocation_num = int(raw_inv) if raw_inv is not None else 1
        except (TypeError, ValueError):
            invocation_num = 1

        if invocation_num <= 1:
            _ensure_cli_statusline_and_yolo_settings(payload)

        conv_id = _resolve_conv_id(payload)
        if conv_id and not payload.get("conversationId"):
            payload = dict(payload, conversationId=conv_id)

        is_subagent = _is_subagent_conversation(payload)
        already_emitted = _has_turn1_been_emitted(conv_id) if conv_id else False

        if raw_inv_is_zero and not is_subagent and not _has_any_user_turn_evidence(payload):
            print(json.dumps({"injectSteps": []}))
            return

        MILESTONE_INVS = {25, 75, 150, 300, 500, 750, 1000}
        is_turn_one = (invocation_num in (0, 1)) and not is_subagent and not already_emitted
        is_subagent_turn_one = (invocation_num in (0, 1)) and is_subagent and not already_emitted

        if is_turn_one:
            _maybe_run_herdr_resume_fallback(conv_id, payload)

        if (is_turn_one or is_subagent_turn_one) and ("unittest" not in sys.modules and "pytest" not in sys.modules or os.environ.get("ANTIGRAVITY_TEST_TMP_REAPER")):
            _reap_stale_tmp_artifacts(max_age_sec=86400)
        if is_turn_one and ("unittest" not in sys.modules and "pytest" not in sys.modules):
            _auto_disable_browseros_mcp(payload)
        is_milestone = (invocation_num in MILESTONE_INVS) or (
            invocation_num > 1000 and invocation_num % 500 == 0
        )

        ws_paths = payload.get("workspacePaths", [])
        workspace = ws_paths[0] if (ws_paths and isinstance(ws_paths, list)) else os.getcwd()
        slug = _resolve_project_slug(workspace)

        plan_alert = ""
        if not is_subagent:
            unverified_plan = _find_unverified_plan(payload, workspace)
            # Skip watchdog for plans living in the agent artifact dir (~/.gemini/antigravity-cli/brain/**)
            if unverified_plan:
                try:
                    plan_str = str(unverified_plan.resolve())
                    brain_cli = os.path.expanduser("~/.gemini/antigravity-cli/brain")
                    if plan_str.startswith(brain_cli) or "/brain/" in plan_str:
                        unverified_plan = None
                except Exception:
                    pass
            if unverified_plan and not _should_suppress_watchdog(unverified_plan):
                plan_fresh = True
                if workspace and unverified_plan.resolve() == (Path(workspace) / "implementation_plan.md").resolve():
                    try:
                        plan_fresh = (time.time() - os.path.getmtime(unverified_plan)) <= 1800
                    except Exception:
                        plan_fresh = False
                if plan_fresh:
                    oracle_script = Path(workspace) / "scripts" / "verification" / "verify-oracle.sh" if workspace else None
                    if oracle_script and oracle_script.is_file():
                        mandate_instruction = (
                            "MANDATE: In Planning Mode, before asking for user approval or proceeding to execution, you MUST invoke "
                            "`bash scripts/verification/verify-oracle.sh --plan` within this turn and append the Oracle critique, directives, "
                            "and sign-off to `implementation_plan.md`."
                        )
                    else:
                        mandate_instruction = (
                            "MANDATE: In Planning Mode, before asking for user approval or proceeding to execution, you MUST "
                            "run an independent oracle-review subagent on the plan (scaffold gates via `python3 ~/.gemini/antigravity/scripts/ensure-verification-gates.py` "
                            "if the project wants script gates) within this turn and append the Oracle critique, directives, "
                            "and sign-off to `implementation_plan.md`."
                        )
                    plan_alert = (
                        f"[Autonomous Oracle Plan Gate Watchdog]\n"
                        f"Implementation plan detected at `{unverified_plan}` without independent Oracle review "
                        "(missing `## Oracle Hardening, Directives & Verification Matrix`).\n"
                        f"{mandate_instruction}"
                    )

        syntax_alert = _check_and_consume_syntax_warning(payload, workspace)
        stale_alert = _check_and_consume_stale_reads(payload)
        context_alert = _check_context_health_alert(payload, is_subagent, invocation_num)
        recovery_alert = _check_post_compaction_recovery(payload)
        heal_alert = _check_and_consume_auto_heal_alert()
        # Priority order: syntax/quality, stale, plan, context, recovery, heal; capped to ~1500 chars
        alerts = _format_and_cap_alerts(
            [syntax_alert, stale_alert, plan_alert, context_alert, recovery_alert, heal_alert],
            max_chars=1500,
        )

        if not (is_turn_one or is_milestone or is_subagent_turn_one):
            if alerts:
                print(json.dumps({
                    "injectSteps": [
                        {
                            "ephemeralMessage": alerts
                        }
                    ]
                }))
            else:
                print(json.dumps({"injectSteps": []}))
            return

        if is_milestone:
            msg = (
                f"[SOL Milestone Checkpoint - Turn {invocation_num}]\n"
                "- Review recent tool outputs and verify progress toward the active goal.\n"
                "- Ensure task checklist remains current before proceeding."
            )
            if alerts:
                msg = f"{alerts}\n\n{msg}"
        elif is_subagent_turn_one:
            if conv_id:
                _mark_turn1_emitted(conv_id)
            capsule = _build_subagent_grounding_capsule(slug, workspace, payload)
            msg = f"{alerts}\n\n{capsule}".strip() if alerts else capsule
        else:
            if conv_id:
                _mark_turn1_emitted(conv_id)
            msg = _build_turn1_grounding(slug, workspace, payload)
            if alerts:
                msg = f"{alerts}\n\n{msg}"

        print(json.dumps({
            "injectSteps": [
                {
                    "ephemeralMessage": msg
                }
            ]
        }))

    except Exception:
        print(json.dumps({"injectSteps": []}))


if __name__ == "__main__":
    main()
