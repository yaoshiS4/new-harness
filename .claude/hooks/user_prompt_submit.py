#!/usr/bin/env python3
"""UserPromptSubmit hook (port of ``pre_invocation_hook.py`` per-turn logic).

Turn 1 injects the ``[Active Knowledge Grounding]`` capsule: SOT docs, dynamic
memory seeds (registry.sqlite), key graph entities (graph.sqlite), agentless
codegraph symbol localization (UG-05), task-harness overlay, Harmony H_gen ⊕
H_env overlay (CP-1/CP-3) and behavioural anti-patterns from the failure ledger.

Every turn surfaces capped alerts (<= 1500 chars): pending syntax/quality
warnings, stale-read tombstones (UG-03), Oracle plan watchdog, context-health
alert (55% / 75%), post-compaction recovery anchor (LOSS-02), auto-heal notice.
Milestone turns (25/75/150/300/500/750/1000) add a SOL checkpoint reminder.
"""
from __future__ import annotations

import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as H  # noqa: E402

MILESTONES = {25, 75, 150, 300, 500, 750, 1000}
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "when", "then", "than", "have", "has", "are", "was",
    "were", "will", "would", "should", "could", "about", "please", "make", "need", "want", "use", "using", "add", "fix",
    "update", "change", "create", "implement", "file", "files", "code", "function", "class", "also", "just", "like",
    "can", "you", "your", "our", "its", "it's", "not", "but", "all", "any", "some", "more", "less", "new", "old",
}


def extract_prompt_keywords(prompt: str) -> list:
    if not prompt:
        return []
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_\-./]{2,}", prompt)
    out = []
    seen = set()
    for tok in tokens:
        t = tok.strip("./-")
        if not t or t.lower() in STOPWORDS or len(t) < 3:
            continue
        if t.lower() in seen:
            continue
        seen.add(t.lower())
        out.append(t)
    camel = [t for t in out if re.search(r"[a-z][A-Z]|_", t) or "." in t or "/" in t]
    rest = [t for t in out if t not in camel]
    return (camel + rest)[:12]


def memory_seeds(slug: str, prompt: str, limit: int = 4) -> list:
    db = H.registry_db_path()
    if not db.is_file():
        return []
    conn = None
    try:
        conn = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=0.5)
        conn.execute("PRAGMA busy_timeout=500;")
        rows = conn.execute("SELECT key, value FROM memory WHERE slug = ? ORDER BY id DESC LIMIT 25;", (slug,)).fetchall()
        if not rows:
            return []
        kws = {k.lower() for k in extract_prompt_keywords(prompt)}
        scored = []
        for idx, (k, v) in enumerate(rows):
            if not k:
                continue
            toks = set(re.findall(r"[a-z0-9_\-.]{2,}", ("%s %s" % (k, v or "")).lower()))
            scored.append((-len(kws & toks), idx, str(k)))
        scored.sort()
        return [s[2] for s in scored[:limit]]
    except Exception:
        return []
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def graph_entities(slug: str, prompt: str, limit: int = 4) -> list:
    gdb = Path(os.path.expanduser("~/.local/share/codex/projects")) / slug / "graph" / "graph.sqlite"
    if not gdb.is_file():
        return []
    conn = None
    try:
        conn = sqlite3.connect("file:%s?mode=ro" % gdb, uri=True, timeout=0.5)
        conn.execute("PRAGMA busy_timeout=500;")
        cur = conn.cursor()
        tables = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        out = []
        kws = [k.lower() for k in extract_prompt_keywords(prompt)][:6]
        for table in ("edges", "triples", "relations"):
            if table not in tables:
                continue
            cols = {r[1] for r in cur.execute("PRAGMA table_info(%s)" % table).fetchall()}
            src = "src" if "src" in cols else ("subject" if "subject" in cols else None)
            dst = "dst" if "dst" in cols else ("object" if "object" in cols else None)
            rel = "rel" if "rel" in cols else ("predicate" if "predicate" in cols else None)
            if not (src and dst and rel):
                continue
            where = " WHERE is_current = 1" if "is_current" in cols else ""
            rows = cur.execute("SELECT %s, %s, %s FROM %s%s ORDER BY rowid DESC LIMIT 200" % (src, rel, dst, table, where)).fetchall()
            for s, r, d in rows:
                text = ("%s %s %s" % (s, r, d)).lower()
                if kws and not any(k in text for k in kws):
                    continue
                out.append("%s -%s-> %s" % (s, r, d))
                if len(out) >= limit:
                    return out
            if not kws:
                return out[:limit]
            break
        return out[:limit]
    except Exception:
        return []
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def codegraph_seed(prompt: str, ws: str) -> str:
    tokens = extract_prompt_keywords(prompt)
    db = H.codegraph_db_path()
    if not tokens or not db.is_file():
        return ""
    conn = None
    try:
        conn = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=0.5)
        conn.execute("PRAGMA busy_timeout=500;")
        cur = conn.cursor()
        cols = [r[1] for r in cur.execute("PRAGMA table_info(symbols);").fetchall()]
        if not cols:
            return ""
        has_ws = "workspace" in cols
        order = "ORDER BY (CASE WHEN LOWER(kind)='heading' THEN 1 ELSE 0 END), %s line ASC LIMIT 5" % ("pagerank DESC," if "pagerank" in cols else "")
        matched = []
        seen = set()
        for exact in (True, False):
            for tok in tokens[:8 if exact else 5]:
                if has_ws:
                    q = "SELECT name, kind, path, line, end_line FROM symbols WHERE (workspace = ? OR ? = '') AND %s %s" % ("LOWER(name) = LOWER(?)" if exact else "name LIKE ?", order)
                    params = (ws, ws, tok if exact else "%%%s%%" % tok)
                else:
                    q = "SELECT name, kind, path, line, end_line FROM symbols WHERE %s %s" % ("LOWER(name) = LOWER(?)" if exact else "name LIKE ?", order)
                    params = (tok if exact else "%%%s%%" % tok,)
                try:
                    for row in cur.execute(q, params).fetchall():
                        key = (row[0], row[2], int(row[3] or 0))
                        if key in seen:
                            continue
                        seen.add(key)
                        matched.append(row)
                except Exception:
                    continue
                if len(matched) >= 5:
                    break
            if len(matched) >= 5:
                break
        if not matched:
            return ""
        entries = []
        for name, kind, path, line, end_line in matched[:5]:
            p = path
            if ws and isinstance(p, str) and p.startswith(ws):
                p = os.path.relpath(p, ws)
            entries.append("%s (%s @ %s:%s-%s)" % (name, kind, p, line, end_line))
        return "Target Symbols (Agentless RepoMap): " + ", ".join(entries)
    except Exception:
        return ""
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def classify_harmony_mode(prompt: str) -> str:
    if prompt and re.search(
        r"\b(?:(?:auth|access|refresh|api|jwt|csrf|bearer|oauth|id|security|secret)[\s_-]*tokens?|auth|security|secret|password|credential|migration|schema|permission|cve|vulnerability|rm|delete|production)\b",
        prompt, re.IGNORECASE,
    ):
        return "strict_security"
    return "balanced_velocity"


def harmony_overlay(slug: str, prompt: str) -> str:
    if not slug or slug in ("global", "default"):
        return ""
    mode = classify_harmony_mode(prompt)
    bullet = ""
    overlay = H.skillbank_dir() / "env_overlays" / ("%s.md" % slug)
    if overlay.is_file():
        try:
            bullets = [l.strip().lstrip("-* ").strip() for l in overlay.read_text(encoding="utf-8").splitlines() if l.strip().startswith(("-", "*"))]
            if bullets:
                bullet = "; ".join(bullets[:2])
                if len(bullet) > 160:
                    bullet = bullet[:157] + "..."
        except Exception:
            pass
    score = ""
    db = H.registry_db_path()
    if db.is_file():
        conn = None
        try:
            conn = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=1.0)
            order = "(CASE WHEN slug = ? THEN 0 ELSE 1 END), %s" % ("sec_score DESC, func_score DESC, token_score DESC" if mode == "strict_security" else "func_score DESC, token_score DESC, sec_score DESC")
            row = conn.execute("SELECT func_score, sec_score, token_score FROM harness_pareto_archive WHERE (slug = ? OR slug = 'global') AND is_pareto_front = 1 ORDER BY %s LIMIT 1;" % order, (slug, slug)).fetchone()
            if row:
                score = "Pareto (%.2f/%.2f/%.2f)" % (row[0], row[1], row[2])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    if not bullet and not score:
        return ""
    summary = "- Harmony Harness (H_gen ⊕ H_env [%s]): %s" % (mode, " | ".join(x for x in (score, bullet) if x))
    return summary[:217] + "..." if len(summary) > 220 else summary


def behavioral_antipatterns(payload: dict, slug: str) -> list:
    out = []
    fb = H.load_state(payload, "structured_feedback", default=None, scoped=False)
    if isinstance(fb, dict):
        ts = float(fb.get("timestamp") or 0.0)
        if ts > 0 and (time.time() - ts) <= 180:
            lbl = str(fb.get("failure_label") or "").strip()
            msg = str(fb.get("message") or "").strip()
            if lbl or msg:
                out.append("Recent Tool Failure [%s]: %s" % (lbl, msg[:80]) if lbl else "Recent Tool Failure: %s" % msg[:80])
    db = H.registry_db_path()
    if db.is_file():
        conn = None
        try:
            conn = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=0.5)
            conn.execute("PRAGMA busy_timeout=500;")
            cur = conn.cursor()
            cols = {r[1] for r in cur.execute("PRAGMA table_info(harness_failures);").fetchall()}
            if cols:
                where = []
                params = []
                if "resolved_at" in cols:
                    where.append("(resolved_at IS NULL OR resolved_at = '')")
                if slug and "slug" in cols:
                    where.append("(slug = ? OR slug = 'global')")
                    params.append(slug)
                if "created_at" in cols:
                    where.append("(created_at IS NULL OR created_at = '' OR datetime(created_at) >= datetime('now', '-7 days'))")
                sql = "SELECT failure_type, reason, COUNT(*) as cnt FROM harness_failures %s GROUP BY failure_type, reason ORDER BY cnt DESC LIMIT 3;" % (("WHERE " + " AND ".join(where)) if where else "")
                for ftype, reason, cnt in cur.execute(sql, tuple(params)).fetchall():
                    snippet = "%s (count=%s)" % (ftype or "unknown", cnt)
                    if reason:
                        snippet += ": %s" % str(reason)[:60]
                    out.append("Recurring Failure: " + snippet)
                sid = H.session_id(payload)
                if "conv_id" in cols:
                    tg = cur.execute("SELECT COUNT(*) FROM harness_failures WHERE conv_id = ? AND failure_type IN ('slice_loop_breaker','flood_guard','slice_cap_exceeded','tool_guidance','read_budget_lock')", (sid,)).fetchone()[0]
                    if tg >= 2:
                        out.append("DOM Micro-Tool Hint: repeated tool friction detected; use codegraph:extract_symbols or write a helper script in the scratchpad.")
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    return out[:4]


def build_turn1_grounding(payload: dict, ws: str, slug: str, prompt: str) -> str:
    sot = H.find_sot_docs(ws)
    mem = memory_seeds(slug, prompt)
    ents = graph_entities(slug, prompt)
    lines = [
        "[Active Knowledge Grounding - %s]" % slug,
        "- Dynamic Memory Seeds: %s" % (", ".join("`%s`" % m for m in mem) if mem else "none%s" % (" (refer to %s)" % sot[0] if sot else "")),
        "- Key Graph Entities: %s" % (", ".join(ents) if ents else "none"),
    ]
    if os.path.isfile(os.path.join(ws, "scripts/verification/verify-oracle.sh")):
        lines.append("- SOL Verification Gates: Active (scripts/verification/verify-oracle.sh & test-3-round-loop.sh)")
    seed = codegraph_seed(prompt, ws)
    if seed:
        lines.append("- " + seed)
    for overlay_dir in (os.path.join(ws, ".claude", "harness"), os.path.join(ws, ".antigravity", "task_harness")):
        if os.path.isdir(overlay_dir):
            try:
                files = sorted(f for f in os.listdir(overlay_dir) if not f.startswith("."))
                if files:
                    lines.append(("- Active Task Harness Overlay (%s/): %d file(s) (%s)." % (os.path.relpath(overlay_dir, ws), len(files), ", ".join(files[:3])))[:200])
                    break
            except Exception:
                pass
    harmony = harmony_overlay(slug, prompt)
    if harmony:
        lines.append(harmony)
    anti = behavioral_antipatterns(payload, slug)
    if anti:
        lines.append(("- Behavioral Anti-Patterns: " + "; ".join(anti))[:200])
    if sot:
        lines.append("- Query Protocol: prefer project-local SOT docs (%s) and targeted Grep before broad file scanning." % ", ".join(sot[:2]))
    else:
        lines.append("- Query Protocol: prefer targeted Grep before broad file scanning.")
    lines.append("- Runtime: Claude Code harness v%s. Default output mode: ADHD Mode (action-first). Root thread = PM; delegate code mutation to builder subagents with `allowed_files:` leases." % H.HARNESS_VERSION)
    return "\n".join(lines)


# ----- alerts ---------------------------------------------------------------

def consume_syntax_warning(payload: dict) -> str:
    data = H.load_state(payload, "syntax_pending", default=None, scoped=False)
    if not isinstance(data, dict):
        return ""
    try:
        (H.root_session_dir(payload) / "syntax_pending.json").unlink()
    except Exception:
        pass
    fn = os.path.basename(str(data.get("file") or "unknown"))
    err = str(data.get("error") or "")
    if data.get("kind") == "quality":
        return "[Quality Warning] Quality issue detected after editing `%s`:\n%s\nAddress these before completing your turn." % (fn, err)
    return "[SWE-Agent Syntax Smoke Alert] Broken syntax detected after editing `%s`:\n%s\nYou MUST fix this before running tests or completing your turn." % (fn, err)


def consume_stale_reads(payload: dict) -> str:
    data = H.load_state(payload, "superseded", default={}, scoped=False)
    if not isinstance(data, dict) or not data:
        return ""
    now = time.time()
    items = []
    seen = set()
    changed = False
    for fpath, info in data.items():
        if not isinstance(info, dict):
            continue
        if not info.get("delivered") and (now - float(info.get("mutated_at") or 0)) <= 600:
            b = os.path.basename(fpath)
            if b not in seen:
                seen.add(b)
                items.append("%s (%s lines now)" % (b, info.get("lines", 0)))
            info["delivered"] = True
            changed = True
    if changed:
        H.save_state(payload, "superseded", data, scoped=False)
    if items:
        return "[Stale-Read Tombstone]: earlier Read outputs for [%s] are superseded by recent edits. Rely on the latest edit state, not earlier transcript dumps." % ", ".join(items)
    return ""


def plan_watchdog(payload: dict, ws: str) -> str:
    plan = Path(ws) / "implementation_plan.md"
    if not plan.is_file():
        return ""
    try:
        content = plan.read_text(encoding="utf-8", errors="ignore")
        if len(content.strip()) < 20 or any(m in content for m in ("## Oracle Hardening", "ORACLE REVIEW GATEWAY SIGN-OFF")):
            return ""
        if (time.time() - plan.stat().st_mtime) > 1800:
            return ""
        key = "watchdog_%d" % int(plan.stat().st_mtime)
        if not H.once(payload, key):
            return ""
    except Exception:
        return ""
    has_sh = os.path.isfile(os.path.join(ws, "scripts/verification/verify-oracle.sh"))
    mandate = (
        "MANDATE: before asking for user approval or proceeding to execution, run `bash scripts/verification/verify-oracle.sh --plan` and append the Oracle critique, directives, and sign-off to `implementation_plan.md`."
        if has_sh else
        "MANDATE: before asking for user approval or proceeding to execution, run an independent `oracle-review` subagent on the plan (or `/oracle-review`) and append the Oracle critique, directives, and sign-off to `implementation_plan.md`."
    )
    return "[Autonomous Oracle Plan Gate Watchdog]\nImplementation plan detected at `%s` without independent Oracle review (missing `## Oracle Hardening, Directives & Verification Matrix`).\n%s" % (plan, mandate)


def context_health_alert(payload: dict, turn: int, policy: dict) -> str:
    live = H.live_context_usage(payload)
    pct = 0.0
    try:
        pct = float(live.get("used_percentage") or 0.0)
    except Exception:
        pct = 0.0
    degraded = float(policy.get("context_degraded_pct", 55.0))
    critical = float(policy.get("context_critical_pct", 75.0))
    state = H.load_state(payload, "ctx_alert", default={}, scoped=False) or {}
    fire = False
    severity = "DEGRADED"
    reason = ""
    if pct > 0:
        if pct >= critical and not state.get("crossed_critical"):
            fire, severity, reason = True, "CRITICAL", "context usage %.1f%% >= %.0f%%" % (pct, critical)
            state["crossed_critical"] = True
        elif pct >= degraded and not state.get("crossed_degraded"):
            fire, reason = True, "context usage %.1f%% >= %.0f%%" % (pct, degraded)
            state["crossed_degraded"] = True
        elif pct >= degraded and turn % 10 == 0:
            fire, reason = True, "context usage %.1f%%" % pct
        if pct < degraded:
            state["crossed_degraded"] = False
            state["crossed_critical"] = False
    else:
        if turn >= 40 and not state.get("crossed_critical"):
            fire, severity, reason = True, "CRITICAL", "turn %d without live usage telemetry" % turn
            state["crossed_critical"] = True
        elif turn >= 20 and not state.get("crossed_degraded"):
            fire, reason = True, "turn %d >= 20" % turn
            state["crossed_degraded"] = True
        elif turn >= 20 and turn % 10 == 0:
            fire, reason = True, "turn %d" % turn
    H.save_state(payload, "ctx_alert", state, scoped=False)
    if not fire:
        return ""
    obs = ""
    obs_file = Path(os.path.expanduser("~/.cache/antigravity_observations")) / ("%s.md" % H.session_id(payload))
    if obs_file.is_file():
        try:
            txt = obs_file.read_text(encoding="utf-8").strip()
            if txt:
                obs = "\n[Distilled Observation Prefix]: " + txt[-600:].strip()
        except Exception:
            pass
    return (
        "[Context Health Alert: %s (%s)] -> run context_health:compact_observations + context_health:commit_context_ledger when needed, "
        "delegate heavy multi-file work to subagents, and recommend /compact to the user at the end of the turn.%s" % (severity, reason, obs)
    )


def auto_heal_alert() -> str:
    if H.is_test_env() and not os.environ.get("CLAUDE_HARNESS_TEST_HEAL_ALERT"):
        return ""
    for flag in (H.claude_home() / "last_harness_evolution_alert.flag", Path(os.path.expanduser("~/.gemini/last_harness_evolution_alert.flag"))):
        if flag.is_file():
            try:
                content = flag.read_text(encoding="utf-8").strip()
                flag.unlink()
                if content:
                    return "[Autonomous Harness Self-Heal Notice]\n" + content[:200]
            except Exception:
                pass
    return ""


def recovery_anchor(payload: dict) -> str:
    """Surface the saved snapshot on the first prompt after a compaction (LOSS-02)."""
    if not H.flag_set(payload, "post_compact_pending"):
        return ""
    H.flag_clear(payload, "post_compact_pending")
    snap = H.state_dir() / "session_states" / ("%s.md" % H._sanitize(H.session_id(payload)))
    if not snap.is_file():
        return ""
    try:
        if (time.time() - snap.stat().st_mtime) >= 3600:
            return ""
        content = snap.read_text(encoding="utf-8").strip()
    except Exception:
        return ""
    if not content:
        return ""
    return "[Post-Compaction Recovery Anchor]\nContext was compacted. Saved progress snapshot:\n\n%s\n\nResume from where you left off. Re-read active plan files and do NOT redo completed work." % content


def main() -> None:
    try:
        payload = H.read_payload()
        if not payload:
            return
        if H.is_subagent(payload):
            return
        ws = H.workspace(payload)
        policy = H.guardrail_policy(ws)
        prompt = str(payload.get("prompt") or "")
        if prompt.startswith("/") and len(prompt.split()) == 1:
            return  # bare slash command, keep context lean

        def _bump(cur):
            cur = cur if isinstance(cur, dict) else {}
            cur["turn"] = int(cur.get("turn", 0)) + 1
            cur["last_prompt_ts"] = time.time()
            if payload.get("transcript_path"):
                cur["transcript_path"] = str(payload.get("transcript_path"))
            return cur

        meta = H.update_state(payload, "session_meta", _bump, default={}, scoped=False) or {}
        turn = int(meta.get("turn", 1))
        slug = H.project_slug(ws)

        alerts = H.format_alerts([
            consume_syntax_warning(payload),
            consume_stale_reads(payload),
            plan_watchdog(payload, ws),
            context_health_alert(payload, turn, policy),
            recovery_anchor(payload),
            auto_heal_alert(),
        ], max_chars=1500)

        is_turn_one = turn == 1 and H.once(payload, "turn1_emitted", ttl=12 * 3600)
        is_milestone = turn in MILESTONES or (turn > 1000 and turn % 500 == 0)
        msg = ""
        if is_turn_one:
            msg = build_turn1_grounding(payload, ws, slug, prompt)
        elif is_milestone:
            msg = "[SOL Milestone Checkpoint - Turn %d]\n- Review recent tool outputs and verify progress toward the active goal.\n- Ensure the task checklist (task.md / TodoWrite) is current before proceeding.\n- Consider context_health:commit_context_ledger and a handoff checkpoint." % turn
        if alerts:
            msg = (alerts + "\n\n" + msg).strip() if msg else alerts
        if msg:
            H.emit(H.context_output("UserPromptSubmit", msg))
    except Exception:
        pass


if __name__ == "__main__":
    main()
