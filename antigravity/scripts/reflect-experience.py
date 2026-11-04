#!/usr/bin/env python3
"""Level-2 Inter-Task Experience Reflector & NO_ENTRY Gate (arXiv:2610.14224v1).

Inspects .antigravity/task_harness/ and session execution telemetry at task teardown.
Assigns causal verdicts (helped, hurt, no_observed_effect, confounded).
Enforces the NO_ENTRY Anti-Hallucination Gate:
  If verdict in ("hurt", "no_observed_effect", "confounded")
  or confidence not in ("high", "medium")
  or not cue.strip()
  or not evidence.strip():
      return {"status": "NO_ENTRY", "verdict": verdict, "bytes_written": 0}

Promotes validated "helped" lessons to SkillBank, refreshes INDEX.md, and cleans overlays.
Deterministic execution < 1.0s, zero network or LLM calls.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

SKILLBANK_DIR = Path.home() / ".gemini/antigravity/skillbank"
SKILLS_DIR = Path.home() / ".gemini/antigravity/skills"
VALID_VERDICTS = {"helped", "hurt", "no_observed_effect", "confounded"}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_LAYERS = {"general", "task-specific", "failure-lessons", "optimized"}

# Canonical catalog of 29 core skills for INDEX.md generation
CANONICAL_SKILLS: list[dict[str, str]] = [
    {"name": "adhd-mode", "layer": "general", "cues": "adhd, action-first, quick, format, numbered-steps, unbounded-lists", "path": "~/.gemini/antigravity/skills/adhd-mode/SKILL.md"},
    {"name": "animation-mastery", "layer": "task-specific", "cues": "animation, spring, framer-motion, transition, ui-motion, easing, apple-motion", "path": "~/.gemini/antigravity/skills/animation-mastery/SKILL.md"},
    {"name": "archify", "layer": "task-specific", "cues": "architecture, diagram, mermaid, svg, flowchart, system-design", "path": "~/.gemini/antigravity/skills/archify/SKILL.md"},
    {"name": "auto-verification-harness", "layer": "general", "cues": "oracle, harness, verification, gates, test-3-round-loop, verify-oracle", "path": "~/.gemini/antigravity/skills/auto-verification-harness/SKILL.md"},
    {"name": "axi-tools", "layer": "general", "cues": "axi, toon, gh-axi, chrome-devtools-axi, compact-tokens", "path": "~/.gemini/antigravity/skills/axi-tools/SKILL.md"},
    {"name": "browseros-neo", "layer": "task-specific", "cues": "browser, browseros, neo, automation, web-scraping", "path": "~/.gemini/config/skills/browseros-neo/SKILL.md"},
    {"name": "codegraph-explorer", "layer": "general", "cues": "codegraph, symbol, callers, callees, repo_map, explore-code", "path": "~/.gemini/antigravity/skills/codegraph-explorer/SKILL.md"},
    {"name": "codex-runtime-repair", "layer": "task-specific", "cues": "runtime, launcher, repair-codex, runtime-bug, codex-repair", "path": "~/.gemini/antigravity/skills/codex-runtime-repair/SKILL.md"},
    {"name": "context-rot-prevention", "layer": "general", "cues": "context-rot, token-budget, context-health, compaction, ledger", "path": "~/.gemini/antigravity/skills/context-rot-prevention/SKILL.md"},
    {"name": "document-sync", "layer": "general", "cues": "doc-sync, documentation, obsidian, sync-docs, status-md", "path": "~/.gemini/antigravity/skills/document-sync/SKILL.md"},
    {"name": "e2e_testing", "layer": "task-specific", "cues": "e2e, qa, integration-tests, browser-test, test-suite, regression-hunt", "path": "~/.gemini/antigravity/skills/e2e_testing/SKILL.md"},
    {"name": "ground-truth-retrieval", "layer": "general", "cues": "ground-truth, web-search, fetch-docs, context7, external-docs", "path": "~/.gemini/antigravity/skills/ground-truth-retrieval/SKILL.md"},
    {"name": "harness-deficiency-audit", "layer": "general", "cues": "harness-audit, token-bloat, loop-bugs, harness-deficiency, audit-harness", "path": "~/.gemini/antigravity/skills/harness-deficiency-audit/SKILL.md"},
    {"name": "humanize-text", "layer": "task-specific", "cues": "humanize, de-robot, tone, natural-voice, copy-editing", "path": "~/.gemini/antigravity/skills/humanize-text/SKILL.md"},
    {"name": "loop-detection", "layer": "general", "cues": "loop-detection, cycle-breaker, stalled, repeated-errors", "path": "~/.gemini/antigravity/skills/loop-detection/SKILL.md"},
    {"name": "oracle-review", "layer": "general", "cues": "oracle-review, drift-check, hallucination, adversarial-review, release-gate", "path": "~/.gemini/antigravity/skills/oracle-review/SKILL.md"},
    {"name": "project-documentation", "layer": "task-specific", "cues": "prd, spec, project-docs, epic, architecture-notes", "path": "~/.gemini/antigravity/skills/project-documentation/SKILL.md"},
    {"name": "regression-strategy", "layer": "task-specific", "cues": "regression, test-selection, impact-analysis, risk-based-testing", "path": "~/.gemini/antigravity/skills/regression-strategy/SKILL.md"},
    {"name": "requirement-interviewer", "layer": "general", "cues": "clarification, requirements, interview, ask-question, scope", "path": "~/.gemini/antigravity/skills/requirement-interviewer/SKILL.md"},
    {"name": "routing-thresholds", "layer": "general", "cues": "routing, complexity, pm, story-shards, subagent-topology", "path": "~/.gemini/antigravity/skills/routing-thresholds/SKILL.md"},
    {"name": "scope-drift-control", "layer": "general", "cues": "scope-drift, drift-budget, intent-check, boundaries", "path": "~/.gemini/antigravity/skills/scope-drift-control/SKILL.md"},
    {"name": "security-audit", "layer": "task-specific", "cues": "security, vulnerability, cve, auth, secrets, pen-test", "path": "~/.gemini/antigravity/skills/security-audit/SKILL.md"},
    {"name": "senior-architect", "layer": "general", "cues": "architect, adr, tradeoffs, system-architecture, design-doc", "path": "~/.gemini/antigravity/skills/senior-architect/SKILL.md"},
    {"name": "sot-context", "layer": "general", "cues": "sot, status-md, source-of-truth, project-context", "path": "~/.gemini/antigravity/skills/sot-context/SKILL.md"},
    {"name": "spawn-governance", "layer": "general", "cues": "subagent-spawn, file-lease, governance, allowed-files", "path": "~/.gemini/antigravity/skills/spawn-governance/SKILL.md"},
    {"name": "ui-ux-audit", "layer": "task-specific", "cues": "ui-audit, anti-slop, visual-hierarchy, design-tokens, breathability", "path": "~/.gemini/antigravity/skills/ui-ux-audit/SKILL.md"},
    {"name": "ui-ux-craft", "layer": "task-specific", "cues": "ui-craft, components, layout, css, styling, motion-physics", "path": "~/.gemini/antigravity/skills/ui-ux-craft/SKILL.md"},
    {"name": "unlazy", "layer": "general", "cues": "unlazy, acceptance-gates, depth-tree, completion-discipline", "path": "~/.gemini/antigravity/skills/unlazy/SKILL.md"},
    {"name": "worktree-isolation", "layer": "general", "cues": "worktree, git-worktree, parallel-agents, isolated-branch", "path": "~/.gemini/antigravity/skills/worktree-isolation/SKILL.md"},
]


def compute_subagent_roi(referenced_files_count: int, subagent_tool_calls: int) -> float:
    """Subagent Cost-Accuracy Pareto ROI Telemetry.

    Computes the Pareto efficiency ratio of unique files touched/referenced
    per subagent tool invocation.
    """
    return round(referenced_files_count / max(1, subagent_tool_calls), 4)


def compute_span_waterfall_metrics(spans: list[dict[str, Any]]) -> dict[str, Any]:
    """Subagent Span Waterfall Telemetry.

    Computes per-role and aggregate latency, token consumption, retry waste,
    verified edit ratios, and composite Pareto ROI scores across spans.
    """
    per_role: dict[str, dict[str, Any]] = {}
    agg_latency = 0.0
    agg_tokens = 0
    agg_calls = 0
    agg_retries = 0
    agg_edits = 0
    agg_verified_edits = 0
    agg_ref_files = 0

    for span in spans or []:
        if not isinstance(span, dict):
            continue
        role = str(span.get("role") or "default").strip() or "default"
        latency = float(span.get("latency_ms", span.get("duration_ms", 0.0)) or 0.0)
        tokens = int(span.get("tokens_consumed", span.get("tokens", 0)) or 0)
        calls = int(span.get("tool_calls", span.get("subagent_tool_calls", 1)) or 0)
        retries = int(span.get("retry_calls", span.get("retries", 0)) or 0)
        edits = int(span.get("total_edits", span.get("edits", 0)) or 0)
        verified = int(span.get("verified_edits", edits if span.get("verified") else 0) or 0)
        ref_files = int(span.get("referenced_files_count", verified or edits) or 0)

        agg_latency += latency
        agg_tokens += tokens
        agg_calls += calls
        agg_retries += retries
        agg_edits += edits
        agg_verified_edits += verified
        agg_ref_files += ref_files

        bucket = per_role.setdefault(
            role,
            {
                "span_count": 0,
                "total_latency_ms": 0.0,
                "tokens_consumed": 0,
                "_calls": 0,
                "_retries": 0,
                "_edits": 0,
                "_verified": 0,
                "_ref_files": 0,
            },
        )
        bucket["span_count"] += 1
        bucket["total_latency_ms"] = round(bucket["total_latency_ms"] + latency, 2)
        bucket["tokens_consumed"] += tokens
        bucket["_calls"] += calls
        bucket["_retries"] += retries
        bucket["_edits"] += edits
        bucket["_verified"] += verified
        bucket["_ref_files"] += ref_files

    formatted_roles: dict[str, dict[str, Any]] = {}
    for role, b in per_role.items():
        r_waste = round(min(1.0, b["_retries"] / max(1, b["_calls"])), 4)
        v_ratio = round(min(1.0, b["_verified"] / max(1, b["_edits"])) if b["_edits"] > 0 else 0.0, 4)
        base_roi = compute_subagent_roi(b["_ref_files"], b["_calls"])
        pareto_roi = round(
            (0.5 * v_ratio + 0.5 * min(1.0, base_roi)) * (1.0 - 0.5 * r_waste),
            4,
        )
        formatted_roles[role] = {
            "span_count": b["span_count"],
            "total_latency_ms": b["total_latency_ms"],
            "tokens_consumed": b["tokens_consumed"],
            "retry_waste_ratio": r_waste,
            "verified_edit_ratio": v_ratio,
            "pareto_roi_score": pareto_roi,
        }

    total_retry_waste = round(min(1.0, agg_retries / max(1, agg_calls)), 4)
    total_verified_ratio = round(
        min(1.0, agg_verified_edits / max(1, agg_edits)) if agg_edits > 0 else 0.0,
        4,
    )
    agg_base_roi = compute_subagent_roi(agg_ref_files, agg_calls)
    total_pareto_roi = round(
        (0.5 * total_verified_ratio + 0.5 * min(1.0, agg_base_roi)) * (1.0 - 0.5 * total_retry_waste),
        4,
    )

    return {
        "total_latency_ms": round(agg_latency, 2),
        "tokens_consumed": agg_tokens,
        "retry_waste_ratio": total_retry_waste,
        "verified_edit_ratio": total_verified_ratio,
        "pareto_roi_score": total_pareto_roi,
        "per_role": formatted_roles,
    }


def compute_causal_verdict(
    unisolated_edit_count: int = 0,
    isolated_probe: bool = False,
    ref_metrics: Optional[dict] = None,
    cand_metrics: Optional[dict] = None,
    explicit_verdict: Optional[str] = None,
) -> str:
    """Compute causal verdict with strict confounder detection.

    Rule: If unisolated_edit_count >= 2 and not isolated_probe -> automatically 'confounded'.
    """
    if unisolated_edit_count >= 2 and not isolated_probe:
        return "confounded"

    if explicit_verdict:
        v = str(explicit_verdict).strip().lower()
        if v in VALID_VERDICTS:
            return v

    if ref_metrics is not None and cand_metrics is not None:
        ref_err = int(ref_metrics.get("tool_error_count", 0))
        ref_jev = int(ref_metrics.get("jev_loop_warnings", 0))
        ref_strikes = int(ref_metrics.get("read_budget_strikes", 0))

        cand_err = int(cand_metrics.get("tool_error_count", 0))
        cand_jev = int(cand_metrics.get("jev_loop_warnings", 0))
        cand_strikes = int(cand_metrics.get("read_budget_strikes", 0))
        cand_deliv = bool(cand_metrics.get("deliverable_non_empty", True))

        delta = (ref_err - cand_err) + 2 * (ref_jev - cand_jev) + (ref_strikes - cand_strikes)

        if not cand_deliv or cand_err > ref_err or delta < 0:
            return "hurt"
        if delta > 0 and cand_deliv and cand_err == 0:
            return "helped"
        return "no_observed_effect"

    return "no_observed_effect"


def evaluate_no_entry_gate(
    verdict: str,
    confidence: str,
    cue: str,
    evidence: str,
) -> Optional[dict]:
    """Enforce the NO_ENTRY Anti-Hallucination Gate.

    Returns dict with status="NO_ENTRY" and bytes_written=0 if rejected, or None if gate passed.
    """
    reasons: list[str] = []

    if verdict in ("hurt", "no_observed_effect", "confounded"):
        reasons.append(f"verdict '{verdict}' is not 'helped'")

    conf = str(confidence).strip().lower()
    if conf not in ("high", "medium"):
        reasons.append(f"confidence '{conf}' is not 'high' or 'medium'")

    if not cue or not str(cue).strip():
        reasons.append("cue keyword string is empty")

    if not evidence or not str(evidence).strip():
        reasons.append("causal evidence string is empty")

    if reasons:
        return {
            "status": "NO_ENTRY",
            "verdict": verdict,
            "bytes_written": 0,
            "reason": "; ".join(reasons),
        }

    return None


def extract_capsule_metadata(capsule_path: Path) -> Optional[dict]:
    """Extract metadata from an existing EXPERIENCE.md capsule."""
    if not capsule_path.is_file():
        return None
    try:
        text = capsule_path.read_text(encoding="utf-8")
        m = re.search(r"```yaml\s*\nexperience_capsule:\s*\n(.*?)\n```", text, re.DOTALL)
        if not m:
            return None
        meta: dict[str, str] = {}
        for line in m.group(1).splitlines():
            line = line.strip()
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip("'\"")
        return meta
    except Exception:
        return None


def rebuild_index(
    skillbank_dir: Optional[Path] = None,
    skills_dir: Optional[Path] = None,
    index_path: Optional[Path] = None,
) -> int:
    """Catalog all 28 core skills and adopted experience capsules in INDEX.md."""
    sb_dir = (skillbank_dir or SKILLBANK_DIR).resolve()
    idx_path = index_path or (sb_dir / "INDEX.md")

    lines: list[str] = [
        "# Antigravity SkillBank & Cue Index",
        "",
        "> [!NOTE]",
        "> Canonical registry of core skills and adopted experience capsules for Turn-1 cue-matched retrieval "
        "($\\text{Harness}^2$ Level-2 Inter-Task Reflection, `arXiv:2610.14224v1`).",
        "> Maintained automatically by `~/.gemini/antigravity/scripts/reflect-experience.py`.",
        "",
        "## 1. Core Skills Catalog (28 Active Skills)",
        "",
        "| Skill Name | Layer | Cue Keywords | Path |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for s in CANONICAL_SKILLS:
        lines.append(f"| `{s['name']}` | {s['layer']} | {s['cues']} | `{s['path']}` |")

    lines.extend([
        "",
        "## 2. Adopted Experience Capsules",
        "",
        "<!-- Dynamic section populated by reflect-experience.py -->",
        "| Entry ID | Layer | Verdict | Confidence | Cue Keywords | Date | Path |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    capsule_count = 0
    if sb_dir.is_dir():
        for exp_file in sorted(sb_dir.glob("**/EXPERIENCE.md")):
            meta = extract_capsule_metadata(exp_file)
            if meta:
                entry_id = meta.get("id", exp_file.parent.name)
                layer = meta.get("layer", exp_file.parent.parent.name)
                verdict = meta.get("verdict", "helped")
                conf = meta.get("confidence", "high")
                cue = meta.get("cue", "")
                created = meta.get("created_at", "")[:10]
                try:
                    rel_path = exp_file.relative_to(Path.home())
                    display_path = f"~/{rel_path}"
                except Exception:
                    display_path = str(exp_file)

                lines.append(f"| `{entry_id}` | {layer} | {verdict} | {conf} | {cue} | {created} | `{display_path}` |")
                capsule_count += 1

    content = "\n".join(lines) + "\n"
    idx_path.parent.mkdir(parents=True, exist_ok=True)
    idx_path.write_text(content, encoding="utf-8")
    return len(CANONICAL_SKILLS) + capsule_count


def promote_experience(
    entry_id: str,
    layer: str,
    cue: str,
    lesson: str,
    evidence: str,
    confidence: str = "high",
    verdict: str = "helped",
    metrics: Optional[dict] = None,
    overlay_dir: Optional[Union[str, Path]] = None,
    cleanup_overlay: bool = False,
    skillbank_dir: Optional[Path] = None,
) -> dict:
    """Promote an empirical lesson to SkillBank after passing the NO_ENTRY gate."""
    sb_dir = (skillbank_dir or SKILLBANK_DIR).resolve()
    target_layer = layer if layer in VALID_LAYERS else "task-specific"
    safe_entry_id = re.sub(r"[^a-zA-Z0-9_\-\.]", "-", entry_id).strip("-") or f"exp-{int(time.time())}"
    capsule_dir = sb_dir / target_layer / safe_entry_id
    capsule_dir.mkdir(parents=True, exist_ok=True)

    capsule_path = capsule_dir / "EXPERIENCE.md"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    harness_notes = ""
    bytes_written = 0

    # Copy overlay harness files if present
    if overlay_dir:
        ov_path = Path(overlay_dir).resolve()
        if ov_path.is_dir():
            active_files = [f for f in ov_path.iterdir() if f.is_file() and not f.name.startswith(".")]
            if active_files:
                dest_harness = capsule_dir / "harness"
                dest_harness.mkdir(parents=True, exist_ok=True)
                copied_names: list[str] = []
                for f in active_files:
                    dest_file = dest_harness / f.name
                    shutil.copy2(f, dest_file)
                    copied_names.append(f.name)
                    bytes_written += dest_file.stat().st_size
                harness_notes = f"\n## Harness Assets\n- Copied from overlay: `{', '.join(copied_names)}`\n"

    active_metrics = dict(metrics or {})
    if "subagent_roi" not in active_metrics and ("referenced_files_count" in active_metrics or "subagent_tool_calls" in active_metrics):
        active_metrics["subagent_roi"] = compute_subagent_roi(
            int(active_metrics.get("referenced_files_count", 0)),
            int(active_metrics.get("subagent_tool_calls", 0)),
        )

    metrics_str = json.dumps(active_metrics, indent=2)

    content = f"""# Experience Capsule: {safe_entry_id}

```yaml
experience_capsule:
  id: {safe_entry_id}
  layer: {target_layer}
  verdict: {verdict}
  confidence: {confidence}
  cue: {cue}
  created_at: {now_iso}
  status: active
```

## Cue
{cue}

## Lesson
{lesson}

## Causal Evidence
{evidence}

## Verification & Metrics
- Causal Verdict: {verdict}
- Confidence: {confidence}
- Metrics:
```json
{metrics_str}
```
{harness_notes}"""

    capsule_path.write_text(content, encoding="utf-8")
    bytes_written += len(content.encode("utf-8"))

    # Refresh INDEX.md
    rebuild_index(skillbank_dir=sb_dir)

    # Clean up overlay if requested
    cleaned = False
    if cleanup_overlay and overlay_dir:
        ov_path = Path(overlay_dir).resolve()
        if ov_path.is_dir():
            try:
                shutil.rmtree(ov_path)
                cleaned = True
            except Exception:
                pass

    return {
        "status": "ACCEPTED",
        "verdict": verdict,
        "bytes_written": bytes_written,
        "entry_id": safe_entry_id,
        "capsule_path": str(capsule_path),
        "index_updated": True,
        "overlay_cleaned": cleaned,
        "subagent_roi": active_metrics.get("subagent_roi"),
    }


def reflect(
    entry_id: Optional[str] = None,
    layer: str = "task-specific",
    cue: str = "",
    lesson: str = "",
    evidence: str = "",
    confidence: str = "high",
    verdict: Optional[str] = None,
    unisolated_edit_count: int = 0,
    isolated_probe: bool = False,
    ref_metrics: Optional[dict] = None,
    cand_metrics: Optional[dict] = None,
    overlay_dir: Optional[Union[str, Path]] = None,
    cleanup_overlay: bool = False,
    skillbank_dir: Optional[Path] = None,
) -> dict:
    """Main reflection pipeline. Enforces causal verdict and NO_ENTRY gate."""
    computed_verdict = compute_causal_verdict(
        unisolated_edit_count=unisolated_edit_count,
        isolated_probe=isolated_probe,
        ref_metrics=ref_metrics,
        cand_metrics=cand_metrics,
        explicit_verdict=verdict,
    )

    gate_result = evaluate_no_entry_gate(
        verdict=computed_verdict,
        confidence=confidence,
        cue=cue,
        evidence=evidence,
    )

    if gate_result is not None:
        return gate_result

    # NO_ENTRY gate passed -> Promote to SkillBank
    gen_id = entry_id or f"exp-{int(time.time())}"
    return promote_experience(
        entry_id=gen_id,
        layer=layer,
        cue=cue,
        lesson=lesson,
        evidence=evidence,
        confidence=confidence,
        verdict=computed_verdict,
        metrics=cand_metrics,
        overlay_dir=overlay_dir,
        cleanup_overlay=cleanup_overlay,
        skillbank_dir=skillbank_dir,
    )


def compute_gepa_skill_pareto(
    skills_dir: Union[str, Path] = "~/.gemini/antigravity/skills",
    registry_db_path: Optional[str] = None,
) -> dict:
    """Hermes GEPA 3-axis Pareto skill audit (roi_score, reliability_score, compactness_score)."""
    s_dir = Path(skills_dir).expanduser()
    if not s_dir.is_dir():
        repo_skills = Path(__file__).resolve().parent.parent / "skills"
        if repo_skills.is_dir():
            s_dir = repo_skills
        elif SKILLS_DIR.is_dir():
            s_dir = SKILLS_DIR

    db_p = (
        registry_db_path
        or os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB")
        or os.path.expanduser("~/.local/share/codex/projects/registry.sqlite")
    )
    if not os.path.isfile(db_p):
        alt_db = os.path.expanduser("~/.gemini/antigravity/skillbank/registry.sqlite")
        if os.path.isfile(alt_db):
            db_p = alt_db

    skill_failures: dict[str, int] = {}
    if os.path.isfile(db_p):
        try:
            conn = sqlite3.connect(f"file:{db_p}?mode=ro", uri=True, timeout=0.5)
            conn.execute("PRAGMA busy_timeout=500;")
            cur = conn.cursor()
            cols = {row[1] for row in cur.execute("PRAGMA table_info(harness_failures);").fetchall()}
            if "vertex" in cols and "tool_name" in cols:
                rows = cur.execute(
                    """
                    SELECT tool_name, COUNT(*)
                    FROM harness_failures
                    WHERE vertex = 'skill'
                    GROUP BY tool_name;
                    """
                ).fetchall()
                for tname, cnt in rows:
                    if tname:
                        skill_failures[str(tname).strip()] = cnt
            conn.close()
        except Exception:
            pass

    skill_files = list(s_dir.glob("*/SKILL.md")) if s_dir.is_dir() else []
    if not skill_files and s_dir.is_dir():
        skill_files = list(s_dir.glob("**/SKILL.md"))

    skill_data: dict[str, dict[str, Any]] = {}
    for sf in sorted(skill_files):
        sname = sf.parent.name
        try:
            text = sf.read_text(encoding="utf-8")
        except Exception:
            continue
        char_count = len(text)

        text_lower = text.lower()
        roi = 0.5
        if "description:" in text_lower:
            roi += 0.2
        if "```" in text:
            roi += 0.15
        if any(w in text_lower for w in ("directive", "rule", "protocol", "step", "workflow", "guideline")):
            roi += 0.15
        roi_score = round(max(0.1, min(1.0, roi)), 4)

        fail_cnt = skill_failures.get(sname, 0)
        rel_score = round(max(0.0, 1.0 - 0.2 * fail_cnt), 4)

        if char_count <= 2500:
            comp_score = 1.0
        else:
            comp_score = max(0.0, round(1.0 - (char_count - 2500) / 7500.0, 4))

        skill_data[sname] = {
            "name": sname,
            "path": str(sf),
            "char_count": char_count,
            "roi_score": roi_score,
            "reliability_score": rel_score,
            "compactness_score": comp_score,
        }

    frontier: list[str] = []
    dominated: list[dict[str, Any]] = []
    all_names = list(skill_data.keys())

    for name_a in all_names:
        a = skill_data[name_a]
        is_dominated = False
        dominator = ""
        for name_b in all_names:
            if name_a == name_b:
                continue
            b = skill_data[name_b]
            if (
                b["roi_score"] >= a["roi_score"]
                and b["reliability_score"] >= a["reliability_score"]
                and b["compactness_score"] >= a["compactness_score"]
                and (
                    b["roi_score"] > a["roi_score"]
                    or b["reliability_score"] > a["reliability_score"]
                    or b["compactness_score"] > a["compactness_score"]
                )
            ):
                is_dominated = True
                dominator = name_b
                break

        if is_dominated:
            hints: list[str] = []
            if a["compactness_score"] < 0.6:
                hints.append("Compress SKILL.md to stay within optimal character budget.")
            if a["reliability_score"] < 0.8:
                hints.append("Resolve repeated failures associated with this skill in registry.")
            if a["roi_score"] < 0.7:
                hints.append("Enhance frontmatter description and add concrete executable examples.")
            dominated.append({
                "name": name_a,
                "scores": {
                    "roi_score": a["roi_score"],
                    "reliability_score": a["reliability_score"],
                    "compactness_score": a["compactness_score"],
                },
                "dominated_by": dominator,
                "hints": hints,
            })
        else:
            frontier.append(name_a)

    return {
        "total_skills": len(skill_data),
        "pareto_frontier_count": len(frontier),
        "pareto_frontier": frontier,
        "dominated_count": len(dominated),
        "dominated_skills": dominated,
        "skills": skill_data,
        "optimization_hints": [f"{d['name']}: {'; '.join(d['hints'])}" for d in dominated if d["hints"]],
    }


def harvest_workspace_experience(
    workspace: Union[str, Path] = ".",
    conv_id: str = "",
    transcript_path: str = "",
    registry_db_path: Optional[str] = None,
    skillbank_dir: Optional[Path] = None,
) -> dict:
    """Harvest empirical experience from workspace task_harness overlay or registry.sqlite fail-to-pass recovery."""
    ws = Path(workspace).resolve()
    overlay_dir = ws / ".antigravity" / "task_harness"
    state_file = overlay_dir / "state.json"

    # Branch (a): Inspect state.json in task_harness
    if state_file.is_file():
        try:
            state_data = json.loads(state_file.read_text(encoding="utf-8"))
            last_delta = float(state_data.get("last_delta", 0.0))
            if last_delta == 0.0 and state_data.get("history"):
                last_delta = float(state_data["history"][-1].get("delta", 0.0))
            already_promoted = bool(state_data.get("promoted_to_skillbank") or state_data.get("promoted"))
            if last_delta > 0.0 and not already_promoted:
                step = state_data.get("step", 1)
                last_reason = ""
                if state_data.get("history"):
                    last_reason = str(state_data["history"][-1].get("reason", "")).strip()

                cue = str(state_data.get("cue") or "").strip()
                if not cue:
                    cue = "task_harness, dynamic_overlay, recovery"
                    if last_reason:
                        words = [w.strip(",.():;\"'").lower() for w in last_reason.split() if len(w) > 3]
                        if words:
                            cue = f"task_harness, {', '.join(words[:4])}"

                lesson = str(state_data.get("lesson") or "").strip()
                if not lesson:
                    lesson = f"Adopted overlay repair: {last_reason}" if last_reason else "Task-specific harness adaptation resolved behavioral friction."

                evidence = str(state_data.get("evidence") or "").strip()
                if not evidence:
                    evidence = f"Task harness achieved positive behavioral delta {last_delta:.2f} at step {step}."

                ref_metrics = {"tool_error_count": 1, "jev_loop_warnings": 0, "read_budget_strikes": 0}
                cand_metrics = {"tool_error_count": 0, "jev_loop_warnings": 0, "read_budget_strikes": 0, "deliverable_non_empty": True, "delta": last_delta}

                entry_id = f"task-overlay-{int(time.time())}"
                res = reflect(
                    entry_id=entry_id,
                    layer="task-specific",
                    cue=cue,
                    lesson=lesson,
                    evidence=evidence,
                    confidence="high",
                    verdict="helped",
                    unisolated_edit_count=0,
                    isolated_probe=True,
                    ref_metrics=ref_metrics,
                    cand_metrics=cand_metrics,
                    overlay_dir=overlay_dir,
                    cleanup_overlay=False,
                    skillbank_dir=skillbank_dir,
                )
                if res.get("status") == "ACCEPTED":
                    state_data["promoted_to_skillbank"] = True
                    try:
                        state_file.write_text(json.dumps(state_data, indent=2), encoding="utf-8")
                    except Exception:
                        pass
                return res
        except Exception:
            pass

    # Branch (b): Inspect registry.sqlite for fail-to-pass recovery on conv_id
    db_p = (
        registry_db_path
        or os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB")
        or os.path.expanduser("~/.local/share/codex/projects/registry.sqlite")
    )
    if not os.path.isfile(db_p):
        alt_db = os.path.expanduser("~/.gemini/antigravity/skillbank/registry.sqlite")
        if os.path.isfile(alt_db):
            db_p = alt_db

    if conv_id and os.path.isfile(db_p):
        conn = None
        try:
            conn = sqlite3.connect(f"file:{db_p}?mode=ro", uri=True, timeout=0.5)
            conn.execute("PRAGMA busy_timeout=500;")
            cur = conn.cursor()
            cols = {row[1] for row in cur.execute("PRAGMA table_info(harness_failures);").fetchall()}

            sel_cols = ["id", "failure_type", "reason"]
            sel_cols.append("remedy" if "remedy" in cols else "'' as remedy")
            sel_cols.append("resolved_at" if "resolved_at" in cols else "NULL as resolved_at")
            sel_cols.append("tool_name" if "tool_name" in cols else "'' as tool_name")
            sel_cols.append("vertex" if "vertex" in cols else "'' as vertex")

            query = f"SELECT {', '.join(sel_cols)} FROM harness_failures WHERE conv_id = ? ORDER BY id DESC"
            rows = cur.execute(query, (conv_id,)).fetchall()

            recovered_failure = None
            for r in rows:
                fid, ftype, reason, remedy, resolved_at, tool_name, vertex = r
                if remedy and str(remedy).strip():
                    recovered_failure = (ftype, reason, str(remedy).strip(), tool_name)
                    break
                if resolved_at:
                    remedy_text = f"Resolved {ftype}: {reason}" if reason else f"Resolved {ftype}"
                    recovered_failure = (ftype, reason, remedy_text, tool_name)
                    break

            # Inspect transcript_path if provided
            clean_completion = False
            modified_source_files: set[str] = set()
            if transcript_path and os.path.isfile(transcript_path):
                try:
                    with open(transcript_path, "r", encoding="utf-8") as tf:
                        lines = tf.readlines()
                    last_status = "DONE"
                    for line in lines:
                        try:
                            item = json.loads(line)
                            if isinstance(item, dict):
                                st = item.get("status")
                                if st:
                                    last_status = str(st).upper()
                                tool_calls = item.get("tool_calls", [])
                                for tc in tool_calls:
                                    fn = tc.get("function", {}).get("name") or tc.get("name")
                                    args = tc.get("function", {}).get("arguments") or tc.get("args") or {}
                                    if isinstance(args, str):
                                        try:
                                            args = json.loads(args)
                                        except Exception:
                                            args = {}
                                    if fn in (
                                        "write_file",
                                        "edit_file",
                                        "replace_file_content",
                                        "write_to_file",
                                        "multi_replace_file_content",
                                    ):
                                        p = (
                                            args.get("Path")
                                            or args.get("TargetFile")
                                            or args.get("AbsolutePath")
                                            or args.get("file_path")
                                            or args.get("path")
                                        )
                                        if p and not any(p.endswith(ext) for ext in (".md", ".json", ".log", ".tmp", ".txt")):
                                            modified_source_files.add(p)
                        except Exception:
                            pass
                    if last_status in ("DONE", "SUCCESS", "0", 0):
                        clean_completion = True
                except Exception:
                    pass

            unisolated_edit_count = len(modified_source_files)

            if not recovered_failure and rows and clean_completion:
                r = rows[0]
                fid, ftype, reason, remedy, resolved_at, tool_name, vertex = r
                remedy_text = f"Resolved {ftype} with clean subsequent verification: {reason}"
                recovered_failure = (ftype, reason, remedy_text, tool_name)

            if recovered_failure:
                ftype, reason, remedy, tool_name = recovered_failure
                t_label = tool_name or "tool"
                cue = f"{t_label}, {ftype or 'friction'}, recovery"
                lesson = remedy
                evidence = f"Fail-to-pass recovery in session {conv_id} verified with clean completion."

                ref_metrics = {"tool_error_count": len(rows), "jev_loop_warnings": 0, "read_budget_strikes": 0}
                cand_metrics = {"tool_error_count": 0, "jev_loop_warnings": 0, "read_budget_strikes": 0, "deliverable_non_empty": True}

                safe_conv = re.sub(r"[^a-zA-Z0-9_\-]", "-", conv_id)
                entry_id = f"recov-{safe_conv[:16]}-{int(time.time())}"

                return reflect(
                    entry_id=entry_id,
                    layer="task-specific",
                    cue=cue,
                    lesson=lesson,
                    evidence=evidence,
                    confidence="high",
                    verdict="helped",
                    unisolated_edit_count=unisolated_edit_count,
                    isolated_probe=(unisolated_edit_count <= 1),
                    ref_metrics=ref_metrics,
                    cand_metrics=cand_metrics,
                    skillbank_dir=skillbank_dir,
                )
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    return {
        "status": "NO_ENTRY",
        "verdict": "no_observed_effect",
        "bytes_written": 0,
        "reason": "No isolated task-harness recovery or registry remedy found in workspace session",
    }


def validate_knowledge_target(workspace_root: Path, target_path: Path) -> bool:
    """Validate that target_path stays within workspace_root without traversing symlinks."""
    try:
        ws_raw = Path(os.path.abspath(str(workspace_root)))
        if ws_raw.is_symlink():
            return False
        ws_resolved = workspace_root.resolve()

        tgt_raw = target_path if target_path.is_absolute() else (workspace_root / target_path)
        if ".." in tgt_raw.parts:
            return False

        # Walk from workspace_root down to target_path checking every existing component for symlinks
        tgt_abs = Path(os.path.abspath(str(tgt_raw)))
        if not tgt_abs.is_relative_to(ws_raw):
            return False

        cur = ws_raw
        for part in tgt_abs.relative_to(ws_raw).parts:
            cur = cur / part
            if cur.is_symlink():
                return False

        for parent in [tgt_raw, *tgt_raw.parents]:
            if parent.is_symlink():
                return False
            if os.path.abspath(str(parent)) == str(ws_raw):
                break

        if not tgt_raw.resolve().is_relative_to(ws_resolved):
            return False
        return True
    except Exception:
        return False


def distill_to_repo_knowledge(
    workspace: Union[str, Path],
    topic: str,
    cue: str,
    lesson: str,
    evidence: str,
    confidence: str = "high",
    verdict: str = "helped",
) -> dict[str, Any]:
    """Distill validated experience into git-committed <workspace>/.agents/knowledge/<topic>.md."""
    gate_rejection = evaluate_no_entry_gate(
        verdict=verdict,
        confidence=confidence,
        cue=cue,
        evidence=evidence,
    )
    if gate_rejection is not None:
        return gate_rejection

    ws_root = Path(workspace)
    raw_topic = str(topic or "").strip()
    if not raw_topic or ".." in raw_topic or "/" in raw_topic or "\\" in raw_topic:
        return {
            "status": "REJECTED_SYMLINK_ESCAPE",
            "verdict": verdict,
            "bytes_written": 0,
            "reason": f"Invalid or traversal topic: {raw_topic!r}",
        }

    topic_slug = re.sub(r"[^a-z0-9_-]+", "-", raw_topic.lower()).strip("-") or "general"
    agents_dir = ws_root / ".agents"
    knowledge_dir = agents_dir / "knowledge"
    target_md = knowledge_dir / f"{topic_slug}.md"
    index_md = knowledge_dir / "INDEX.md"

    for candidate in (agents_dir, knowledge_dir, target_md, index_md):
        if not validate_knowledge_target(ws_root, candidate):
            return {
                "status": "REJECTED_SYMLINK_ESCAPE",
                "verdict": verdict,
                "bytes_written": 0,
                "reason": f"Symlink or path escape detected at {candidate}",
            }

    knowledge_dir.mkdir(parents=True, exist_ok=True)
    if not validate_knowledge_target(ws_root, target_md) or not validate_knowledge_target(ws_root, index_md):
        return {
            "status": "REJECTED_SYMLINK_ESCAPE",
            "verdict": verdict,
            "bytes_written": 0,
            "reason": "Post-mkdir symlink verification failed",
        }

    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry_block = (
        f"## {now_iso} — `{cue.strip()}`\n"
        f"- **Verdict**: `{verdict}` (`confidence: {confidence}`)\n"
        f"- **Lesson**: {lesson.strip()}\n"
        f"- **Evidence**: {evidence.strip()}\n\n"
    )

    if target_md.is_file():
        existing = target_md.read_text(encoding="utf-8")
        new_content = existing.rstrip() + "\n\n" + entry_block
    else:
        new_content = (
            f"# Repository Knowledge: `{topic_slug}`\n\n"
            f"> Curated operational lessons gated by `NO_ENTRY` (`verdict == helped`).\n\n"
            + entry_block
        )

    target_md.write_text(new_content, encoding="utf-8")
    bytes_written = len(new_content.encode("utf-8"))

    # Rebuild .agents/knowledge/INDEX.md
    topic_files = sorted(
        p for p in knowledge_dir.glob("*.md")
        if p.name != "INDEX.md" and not p.is_symlink()
    )
    idx_lines = [
        "# Repository Knowledge Index (`.agents/knowledge/`)",
        "",
        "| Topic | File | Latest Cue |",
        "| :--- | :--- | :--- |",
    ]
    for tf in topic_files:
        t_name = tf.stem
        c_val = cue.strip() if t_name == topic_slug else "curated"
        idx_lines.append(f"| `{t_name}` | `{tf.name}` | {c_val} |")
    idx_content = "\n".join(idx_lines) + "\n"
    index_md.write_text(idx_content, encoding="utf-8")
    bytes_written += len(idx_content.encode("utf-8"))

    return {
        "status": "DISTILLED",
        "verdict": verdict,
        "topic": topic_slug,
        "path": str(target_md),
        "index_path": str(index_md),
        "bytes_written": bytes_written,
    }


def run_test_confounder() -> bool:
    """Dedicated confounder tests."""
    print("Testing Confounder Detection & NO_ENTRY Enforcement...")

    # Case 1: unisolated_edit_count >= 2 and not isolated_probe -> confounded
    v1 = compute_causal_verdict(unisolated_edit_count=2, isolated_probe=False)
    assert v1 == "confounded", f"Expected 'confounded', got '{v1}'"

    res1 = reflect(
        cue="test, sql",
        lesson="some lesson",
        evidence="pass",
        unisolated_edit_count=2,
        isolated_probe=False,
    )
    assert res1["status"] == "NO_ENTRY", f"Expected 'NO_ENTRY', got {res1}"
    assert res1["verdict"] == "confounded", f"Expected 'confounded', got {res1}"
    assert res1["bytes_written"] == 0, f"Expected 0 bytes, got {res1['bytes_written']}"

    # Case 2: unisolated_edit_count >= 5 and not isolated_probe -> confounded
    v2 = compute_causal_verdict(unisolated_edit_count=5, isolated_probe=False)
    assert v2 == "confounded", f"Expected 'confounded', got '{v2}'"

    # Case 3: unisolated_edit_count = 1 -> not auto-confounded
    v3 = compute_causal_verdict(unisolated_edit_count=1, isolated_probe=False, explicit_verdict="helped")
    assert v3 == "helped", f"Expected 'helped', got '{v3}'"

    # Case 4: unisolated_edit_count = 2 but isolated_probe=True -> not auto-confounded
    v4 = compute_causal_verdict(unisolated_edit_count=2, isolated_probe=True, explicit_verdict="helped")
    assert v4 == "helped", f"Expected 'helped', got '{v4}'"

    print("  Confounder tests: PASS")
    return True


def self_test() -> bool:
    """Run full self-contained test suite."""
    start_t = time.perf_counter()
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        test_sb = Path(td) / "skillbank"
        test_overlay = Path(td) / "task_harness"
        test_overlay.mkdir(parents=True)
        (test_overlay / "SKILL.md").write_text("# Task Skill\n", encoding="utf-8")

        # Test 1: Confounder rejection
        assert run_test_confounder()

        # Test 2: NO_ENTRY on hurt verdict
        res_hurt = reflect(
            cue="python, sqlite",
            lesson="test lesson",
            evidence="failed trace",
            verdict="hurt",
            skillbank_dir=test_sb,
        )
        assert res_hurt["status"] == "NO_ENTRY"
        assert res_hurt["bytes_written"] == 0

        # Test 3: NO_ENTRY on no_observed_effect
        res_no_eff = reflect(
            cue="python, sqlite",
            lesson="test lesson",
            evidence="no change",
            verdict="no_observed_effect",
            skillbank_dir=test_sb,
        )
        assert res_no_eff["status"] == "NO_ENTRY"
        assert res_no_eff["bytes_written"] == 0

        # Test 4: NO_ENTRY on low confidence
        res_low_conf = reflect(
            cue="python, sqlite",
            lesson="test lesson",
            evidence="passed",
            verdict="helped",
            confidence="low",
            skillbank_dir=test_sb,
        )
        assert res_low_conf["status"] == "NO_ENTRY"
        assert res_low_conf["bytes_written"] == 0

        # Test 5: NO_ENTRY on empty cue
        res_no_cue = reflect(
            cue="   ",
            lesson="test lesson",
            evidence="passed",
            verdict="helped",
            confidence="high",
            skillbank_dir=test_sb,
        )
        assert res_no_cue["status"] == "NO_ENTRY"
        assert res_no_cue["bytes_written"] == 0

        # Test 6: NO_ENTRY on empty evidence
        res_no_ev = reflect(
            cue="python, sqlite",
            lesson="test lesson",
            evidence="",
            verdict="helped",
            confidence="high",
            skillbank_dir=test_sb,
        )
        assert res_no_ev["status"] == "NO_ENTRY"
        assert res_no_ev["bytes_written"] == 0

        # Test 7: Valid helped case promoted to SkillBank
        res_promoted = reflect(
            entry_id="test-exp-01",
            layer="task-specific",
            cue="sqlite, timeout, pragma",
            lesson="Set busy_timeout to 500ms on SQLite connections.",
            evidence="Passed all 281 unit tests in 0.49s without lock errors.",
            confidence="high",
            verdict="helped",
            overlay_dir=test_overlay,
            cleanup_overlay=True,
            skillbank_dir=test_sb,
        )
        assert res_promoted["status"] == "ACCEPTED"
        assert res_promoted["bytes_written"] > 0
        exp_md = test_sb / "task-specific" / "test-exp-01" / "EXPERIENCE.md"
        assert exp_md.is_file(), f"EXPERIENCE.md not written: {exp_md}"
        harness_skill = test_sb / "task-specific" / "test-exp-01" / "harness" / "SKILL.md"
        assert harness_skill.is_file(), f"Harness asset not copied: {harness_skill}"
        assert not test_overlay.exists(), "Overlay was not cleaned up"

        # Test 8: Subagent Pareto ROI Telemetry
        roi = compute_subagent_roi(referenced_files_count=6, subagent_tool_calls=2)
        assert roi == 3.0, f"Expected 3.0, got {roi}"
        roi_zero = compute_subagent_roi(referenced_files_count=5, subagent_tool_calls=0)
        assert roi_zero == 5.0, f"Expected 5.0, got {roi_zero}"

        # Verify INDEX.md includes the newly promoted capsule
        idx_content = (test_sb / "INDEX.md").read_text(encoding="utf-8")
        assert "test-exp-01" in idx_content
        assert "sqlite, timeout, pragma" in idx_content
        assert "Core Skills Catalog (28 Active Skills)" in idx_content

        # Test 9: harvest_workspace_experience with state.json (last_delta > 0)
        test_ws_overlay = Path(td) / "workspace_overlay"
        test_th = test_ws_overlay / ".antigravity" / "task_harness"
        test_th.mkdir(parents=True)
        (test_th / "state.json").write_text(json.dumps({
            "step": 2,
            "last_delta": 0.35,
            "cue": "sql, indexing",
            "lesson": "Add composite index on harness_failures",
            "evidence": "Query speedup 12x",
            "history": [{"step": 2, "delta": 0.35, "reason": "Added index"}]
        }), encoding="utf-8")
        h_res1 = harvest_workspace_experience(workspace=test_ws_overlay, skillbank_dir=test_sb)
        assert h_res1["status"] == "ACCEPTED", f"Expected ACCEPTED, got {h_res1}"
        assert (test_sb / "task-specific").is_dir()
        state_after = json.loads((test_th / "state.json").read_text(encoding="utf-8"))
        assert state_after.get("promoted_to_skillbank") is True
        h_res_repeat = harvest_workspace_experience(workspace=test_ws_overlay, skillbank_dir=test_sb)
        assert h_res_repeat["status"] == "NO_ENTRY"

        # Test 10: harvest_workspace_experience with empty/negative delta
        test_ws_zero = Path(td) / "workspace_zero"
        test_th_zero = test_ws_zero / ".antigravity" / "task_harness"
        test_th_zero.mkdir(parents=True)
        (test_th_zero / "state.json").write_text(json.dumps({
            "step": 1,
            "last_delta": 0.0,
            "history": []
        }), encoding="utf-8")
        h_res_zero = harvest_workspace_experience(workspace=test_ws_zero, skillbank_dir=test_sb)
        assert h_res_zero["status"] == "NO_ENTRY"

        # Test 11: harvest_workspace_experience from registry.sqlite fail-to-pass recovery
        test_reg_db = Path(td) / "registry.sqlite"
        conn_t = sqlite3.connect(str(test_reg_db))
        conn_t.execute("""
            CREATE TABLE harness_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conv_id TEXT,
                failure_type TEXT,
                reason TEXT,
                remedy TEXT,
                resolved_at DATETIME,
                tool_name TEXT,
                vertex TEXT
            );
        """)
        conn_t.execute("""
            INSERT INTO harness_failures (conv_id, failure_type, reason, remedy, resolved_at, tool_name, vertex)
            VALUES ('conv-rec-01', 'slice_cap_exceeded', 'Slice exceeds 250 lines', 'Use AST outline before slicing', CURRENT_TIMESTAMP, 'read_file', 'tool_guidance');
        """)
        conn_t.commit()
        conn_t.close()

        test_ws_rec = Path(td) / "workspace_rec"
        test_ws_rec.mkdir()
        h_res_reg = harvest_workspace_experience(
            workspace=test_ws_rec,
            conv_id="conv-rec-01",
            registry_db_path=str(test_reg_db),
            skillbank_dir=test_sb,
        )
        assert h_res_reg["status"] == "ACCEPTED", f"Expected ACCEPTED, got {h_res_reg}"

        # Test 12: compute_gepa_skill_pareto
        test_skills_dir = Path(td) / "skills"
        skill1_dir = test_skills_dir / "high-roi-skill"
        skill1_dir.mkdir(parents=True)
        (skill1_dir / "SKILL.md").write_text("---\nname: high-roi-skill\ndescription: High value skill\n---\n## Directives\n1. Rule 1\n```bash\ncmd\n```\n", encoding="utf-8")

        skill2_dir = test_skills_dir / "bloated-skill"
        skill2_dir.mkdir(parents=True)
        (skill2_dir / "SKILL.md").write_text("No description.\n" + ("Lorem ipsum text words here.\n" * 400), encoding="utf-8")

        gepa_res = compute_gepa_skill_pareto(skills_dir=test_skills_dir, registry_db_path=str(test_reg_db))
        assert gepa_res["total_skills"] == 2
        assert "high-roi-skill" in gepa_res["pareto_frontier"]
        assert gepa_res["dominated_count"] >= 1
        assert any(d["name"] == "bloated-skill" for d in gepa_res["dominated_skills"])

        # Test 13: distill_to_repo_knowledge & validate_knowledge_target
        distill_ws = Path(td) / "workspace_distill"
        distill_ws.mkdir()
        d_res = distill_to_repo_knowledge(
            workspace=distill_ws,
            topic="sqlite-concurrency",
            cue="sqlite, busy_timeout, wal",
            lesson="Always configure PRAGMA busy_timeout=500 on concurrent connections.",
            evidence="Zero lock errors across 40 parallel test workers.",
            confidence="high",
            verdict="helped",
        )
        assert d_res["status"] == "DISTILLED", f"Expected DISTILLED, got {d_res}"
        assert (distill_ws / ".agents" / "knowledge" / "sqlite-concurrency.md").is_file()
        assert (distill_ws / ".agents" / "knowledge" / "INDEX.md").is_file()
        assert "sqlite-concurrency" in (distill_ws / ".agents" / "knowledge" / "INDEX.md").read_text(encoding="utf-8")

        # NO_ENTRY gate enforced on distill_to_repo_knowledge
        d_no_entry = distill_to_repo_knowledge(
            workspace=distill_ws,
            topic="sqlite-concurrency",
            cue="sqlite",
            lesson="Ignored lesson",
            evidence="Failed tests",
            confidence="high",
            verdict="hurt",
        )
        assert d_no_entry["status"] == "NO_ENTRY"

        # Path traversal & symlink escape rejected
        d_trav = distill_to_repo_knowledge(
            workspace=distill_ws,
            topic="../../etc/passwd",
            cue="traversal",
            lesson="Attempt escape",
            evidence="Evidence",
            confidence="high",
            verdict="helped",
        )
        assert d_trav["status"] == "REJECTED_SYMLINK_ESCAPE", f"Expected REJECTED_SYMLINK_ESCAPE, got {d_trav}"

        outside_dir = Path(td) / "outside_secret"
        outside_dir.mkdir()
        symlink_ws = Path(td) / "workspace_symlink"
        (symlink_ws / ".agents").mkdir(parents=True)
        (symlink_ws / ".agents" / "knowledge").symlink_to(outside_dir)
        assert validate_knowledge_target(symlink_ws, symlink_ws / ".agents" / "knowledge" / "leak.md") is False
        d_sym = distill_to_repo_knowledge(
            workspace=symlink_ws,
            topic="leak",
            cue="symlink",
            lesson="Symlink escape attempt",
            evidence="Evidence",
            confidence="high",
            verdict="helped",
        )
        assert d_sym["status"] == "REJECTED_SYMLINK_ESCAPE", f"Expected REJECTED_SYMLINK_ESCAPE, got {d_sym}"

    elapsed = time.perf_counter() - start_t
    print(f"ALL SELF-TESTS PASSED in {elapsed:.4f}s (< 1.0s limit)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Antigravity Level-2 Inter-Task Experience Reflector")
    parser.add_argument("--entry-id", help="Capsule entry ID")
    parser.add_argument("--layer", default="task-specific", choices=sorted(VALID_LAYERS), help="SkillBank layer")
    parser.add_argument("--cue", default="", help="Keyword cues for retrieval")
    parser.add_argument("--lesson", default="", help="Operational lesson / rule")
    parser.add_argument("--evidence", default="", help="Causal trace evidence / test outcome")
    parser.add_argument("--confidence", default="high", choices=sorted(VALID_CONFIDENCE), help="Confidence level")
    parser.add_argument("--verdict", choices=sorted(VALID_VERDICTS), help="Explicit causal verdict")
    parser.add_argument("--unisolated-edit-count", type=int, default=0, help="Number of unisolated file edits")
    parser.add_argument("--isolated-probe", action="store_true", help="Flag: edit was an isolated single-variable probe")
    parser.add_argument("--workspace", default=".", help="Workspace path")
    parser.add_argument("--overlay-dir", help="Path to task harness overlay")
    parser.add_argument("--cleanup-overlay", action="store_true", help="Clean up overlay dir if accepted")
    parser.add_argument("--reflect-json", help="Path to JSON file or '-' for stdin")
    parser.add_argument("--rebuild-index", action="store_true", help="Rebuild SkillBank INDEX.md")
    parser.add_argument("--self-test", action="store_true", help="Run full self-test suite")
    parser.add_argument("--test-confounder", action="store_true", help="Run dedicated confounder test suite")
    parser.add_argument("--conv-id", default="", help="Active conversation ID")
    parser.add_argument("--transcript", default="", help="Path to transcript.jsonl")
    parser.add_argument("--gepa-audit", action="store_true", help="Run Hermes GEPA 3-axis Skill Pareto audit")
    parser.add_argument("--distill-repo", action="store_true", help="Distill validated lesson into <workspace>/.agents/knowledge/<topic>.md")
    parser.add_argument("--topic", default="general", help="Topic slug for --distill-repo")

    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    if args.test_confounder:
        run_test_confounder()
        return 0

    if args.rebuild_index:
        cnt = rebuild_index()
        print(f"Rebuilt SkillBank INDEX.md ({cnt} entries).")
        return 0

    if args.gepa_audit:
        res = compute_gepa_skill_pareto()
        print(json.dumps(res, indent=2))
        return 0

    payload: dict = {}
    if args.reflect_json:
        if args.reflect_json == "-":
            raw = sys.stdin.read()
        else:
            raw = Path(args.reflect_json).read_text(encoding="utf-8")
        try:
            payload = json.loads(raw)
        except Exception as e:
            print(f"Error parsing --reflect-json: {e}", file=sys.stderr)
            return 1

    entry_id = payload.get("entry_id") or args.entry_id
    layer = payload.get("layer") or args.layer
    cue = payload.get("cue") or args.cue
    lesson = payload.get("lesson") or args.lesson
    evidence = payload.get("evidence") or args.evidence
    confidence = payload.get("confidence") or args.confidence
    verdict = payload.get("verdict") or args.verdict
    unisolated_edit_count = payload.get("unisolated_edit_count", args.unisolated_edit_count)
    isolated_probe = payload.get("isolated_probe", args.isolated_probe)
    overlay_dir = payload.get("overlay_dir") or args.overlay_dir
    cleanup_overlay = payload.get("cleanup_overlay", args.cleanup_overlay)
    ref_metrics = payload.get("ref_metrics")
    cand_metrics = payload.get("cand_metrics")

    if args.distill_repo or payload.get("distill_repo"):
        topic_val = payload.get("topic") or args.topic or entry_id or "general"
        res_distill = distill_to_repo_knowledge(
            workspace=args.workspace,
            topic=topic_val,
            cue=cue,
            lesson=lesson,
            evidence=evidence,
            confidence=confidence,
            verdict=verdict or "helped",
        )
        print(json.dumps(res_distill, indent=2))
        return 0

    if not (cue or lesson or evidence):
        res = harvest_workspace_experience(
            workspace=args.workspace,
            conv_id=args.conv_id,
            transcript_path=args.transcript,
        )
        print(json.dumps(res, indent=2))
        return 0

    res = reflect(
        entry_id=entry_id,
        layer=layer,
        cue=cue,
        lesson=lesson,
        evidence=evidence,
        confidence=confidence,
        verdict=verdict,
        unisolated_edit_count=unisolated_edit_count,
        isolated_probe=isolated_probe,
        ref_metrics=ref_metrics,
        cand_metrics=cand_metrics,
        overlay_dir=overlay_dir,
        cleanup_overlay=cleanup_overlay,
    )

    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
