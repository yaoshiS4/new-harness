#!/usr/bin/env python3
"""Stop gate for the Claude Code SOTA Harness (port of ``stop_hook.py``).

Gates (each blocks at most once per session via flags, and never when
``stop_hook_active`` is already set for the same gate):
  1. Autonomous Oracle Plan Gate: ``implementation_plan.md`` created/modified
     this session without the ``## Oracle Hardening`` sign-off section.
  2. Teardown Gate: >= N files modified without ``docs/STATUS.md`` update or a
     ``codex_knowledge`` memory capture.
  3. Causal-Past LTL Verification Gate: application code modified without a
     subsequent verification command (or test/QC/oracle subagent); and the
     Anti-Bluffing gate when the last verification failed.
  4. Simplify Gate (CK-03): advisory when the working-tree diff exceeds the
     LOC/file thresholds.

Teardown tasks: session-state snapshot (LOSS-02), observational memory buffer,
lineage fold (best effort), failure harvest, housekeeping trigger, auto-compact
advisory, reflect-experience spawn, optional desktop notification.
"""
from __future__ import annotations

import collections
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as H  # noqa: E402

ORACLE_MARKERS = ("## Oracle Hardening", "ORACLE REVIEW GATEWAY SIGN-OFF", "## 8. Oracle Hardening")


def find_unverified_plan(ws: str, modified: set) -> Optional[Path]:
    candidates = [Path(ws) / "implementation_plan.md", Path(ws) / ".claude" / "harness" / "implementation_plan.md"]
    for m in modified:
        if os.path.basename(m).lower() == "implementation_plan.md":
            candidates.insert(0, Path(m))
    for cand in candidates:
        if not cand.is_file():
            continue
        try:
            content = cand.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if len(content.strip()) < 20:
            continue
        if any(marker in content for marker in ORACLE_MARKERS):
            continue
        is_session_plan = str(cand.resolve()) in {os.path.abspath(m) for m in modified}
        if not is_session_plan:
            try:
                is_session_plan = (time.time() - cand.stat().st_mtime) <= 1800
            except Exception:
                is_session_plan = False
        if is_session_plan:
            return cand
    return None


def analyze_events(events: list) -> dict:
    modified = []
    app_code = []
    verified_after_last_edit = True
    last_verification_failed = False
    status_updated = False
    memory_stored = False
    for ev in events:
        tool = str(ev.get("tool") or "")
        if tool in H.MUTATION_TOOLS:
            f = str(ev.get("file") or "")
            if f:
                if f not in modified:
                    modified.append(f)
                if "status.md" in f.lower():
                    status_updated = True
                if ev.get("app_code"):
                    if f not in app_code:
                        app_code.append(f)
                    verified_after_last_edit = False
                    last_verification_failed = False
        elif tool in H.SHELL_TOOLS:
            if ev.get("verification"):
                verified_after_last_edit = True
                last_verification_failed = bool(ev.get("failed"))
        elif tool in H.AGENT_TOOLS:
            if ev.get("verification"):
                verified_after_last_edit = True
                last_verification_failed = False
        elif tool.startswith("mcp__"):
            if str(ev.get("mcp_tool") or "") in ("memory_store", "knowledge_capture", "commit_context_ledger", "upsert_fact", "handoff_checkpoint"):
                memory_stored = True
    return {
        "modified": modified,
        "app_code": app_code,
        "verified_after_last_edit": verified_after_last_edit,
        "last_verification_failed": last_verification_failed,
        "status_updated": status_updated,
        "memory_stored": memory_stored,
    }


def check_simplify_gate(ws: str, modified: list, policy: dict) -> Optional[str]:
    if not ws or not os.path.isdir(ws) or H.is_harness_path(os.path.abspath(ws).lower() + "/"):
        return None
    try:
        res = subprocess.run(["git", "diff", "--numstat", "HEAD"], cwd=ws, capture_output=True, text=True, timeout=1.5, check=False)
        if res.returncode != 0 or not res.stdout.strip():
            return None
        total = 0
        files = set()
        abs_mod = {os.path.abspath(m) for m in modified}
        lock_suffixes = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "cargo.lock", "poetry.lock", "composer.lock", "gemfile.lock", "go.sum", "uv.lock")
        noise = (".min.js", ".min.css", ".bundle.js", ".map", ".snap", ".pb.go", ".pb.cc", ".pb.h")
        for line in res.stdout.splitlines():
            parts = line.strip().split("\t")
            if len(parts) < 3:
                continue
            added, deleted, fname = parts[0], parts[1], parts[2]
            fabs = os.path.abspath(os.path.join(ws, fname))
            if modified and fabs not in abs_mod:
                continue
            low = fname.lower()
            if low.endswith(lock_suffixes) or low.endswith(noise) or "__snapshots__/" in low:
                continue
            try:
                total += int(added) + int(deleted)
            except ValueError:
                pass
            files.add(fname)
        if total > int(policy.get("simplify_loc_threshold", 400)) and len(files) > int(policy.get("simplify_file_threshold", 8)):
            return (
                "[Simplify Gate Advisory (CK-03)]: large unsimplified diff detected (%d lines across %d files). "
                "Run a simplification pass (/simplify or simplifier-reviewer subagent) on the modified files to eliminate accidental complexity." % (total, len(files))
            )
    except Exception:
        return None
    return None


def write_observation_buffer(payload: dict, events: list) -> Optional[str]:
    sid = H.session_id(payload)
    obs_dir = Path(os.path.expanduser("~/.cache/antigravity_observations"))
    try:
        obs_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        return None
    mutations, verifications, reads = [], [], []
    for ev in events:
        tool = str(ev.get("tool") or "")
        if tool in H.MUTATION_TOOLS and ev.get("file"):
            mutations.append(os.path.basename(str(ev["file"])))
        elif tool in H.SHELL_TOOLS and ev.get("command"):
            verifications.append(str(ev["command"]))
        elif tool in H.READ_TOOLS and ev.get("file"):
            reads.append(os.path.basename(str(ev["file"])))
    dedup_mut = list(dict.fromkeys(m for m in mutations if m))
    read_counts = collections.Counter(r for r in reads if r)
    dedup_reads = ["`%s` (%d reads)" % (f, c) if c > 1 else "`%s`" % f for f, c in read_counts.most_common(12)]
    dedup_ver = []
    seen = set()
    for v in reversed(verifications):
        vn = v.split(";")[0].strip()
        if vn and vn not in seen:
            seen.add(vn)
            dedup_ver.insert(0, vn)
        if len(dedup_ver) >= 6:
            break
    lines = ["# Observational Memory Buffer (%s)" % sid[:8], "", "## Mutations"]
    lines += ["- `%s`" % m for m in dedup_mut[:15]] or ["- None"]
    lines += ["", "## Verifications"]
    lines += ["- `%s`" % v for v in dedup_ver] or ["- None"]
    lines += ["", "## Key Reads"]
    lines += ["- %s" % r for r in dedup_reads] or ["- None"]
    content = "\n".join(lines)
    if len(content) > 2500:
        content = content[:2490] + "\n..."
    try:
        (obs_dir / ("%s.md" % sid)).write_text(content, encoding="utf-8")
        return content
    except Exception:
        return None


def save_session_snapshot(payload: dict, ws: str, events: list) -> None:
    sid = H.session_id(payload)
    snap_dir = H.state_dir() / "session_states"
    try:
        snap_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        return
    plan = None
    for cand in ("implementation_plan.md", "task.md", "PLAN.md"):
        p = os.path.join(ws, cand)
        if os.path.isfile(p):
            plan = p
            break
    modified = []
    recent_cmds = []
    for ev in events:
        tool = str(ev.get("tool") or "")
        if tool in H.MUTATION_TOOLS and ev.get("file") and ev["file"] not in modified:
            modified.append(str(ev["file"]))
        elif tool in H.SHELL_TOOLS and ev.get("command") and ev["command"] not in recent_cmds:
            recent_cmds.append(str(ev["command"]))
    lines = ["# Session State Snapshot (%s)" % sid, "", "## Active Plan", "- Path: `%s`" % plan if plan else "- None", "", "## Modified Files"]
    lines += ["- `%s`" % m for m in modified] or ["- None"]
    lines += ["", "## Recent Verification"]
    lines += ["- `%s`" % c for c in recent_cmds[-5:]] or ["- None"]
    lines.append("")
    try:
        (snap_dir / ("%s.md" % H._sanitize(sid))).write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass


def harvest_failures(payload: dict) -> None:
    try:
        actions = H.load_state(payload, "actions", default=[])
        if isinstance(actions, list) and len(actions) >= 3:
            for i in range(len(actions) - 2):
                w = actions[i:i + 3]
                tools = [a.get("tool") for a in w]
                if tools[0] and tools[0] == tools[1] == tools[2]:
                    args = [json.dumps(a.get("args", {}), sort_keys=True, default=str) for a in w]
                    if args[0] == args[1] == args[2]:
                        if H.once(payload, "harvest_jev"):
                            H.record_harness_failure(payload, "jev_loop", "Harvested unrecorded Jev loop repetition from session action log", tool_name=str(tools[0]), severity_tier="S0_catastrophic", vertex="skill")
                        break
        reads = H.load_state(payload, "reads", default={})
        if isinstance(reads, dict):
            for fpath, entry in reads.items():
                if isinstance(entry, dict) and int(entry.get("read_count", 0)) >= 3 and H.once(payload, "harvest_read_%s" % os.path.basename(fpath)):
                    H.record_harness_failure(payload, "read_budget_strike", "Harvested read budget strike (%d reads) on %s" % (int(entry.get("read_count", 0)), os.path.basename(fpath)), tool_name="Read", severity_tier="S2_major", vertex="tool_guidance")
    except Exception:
        pass


def fold_lineage(payload: dict, ws: str, events: list) -> None:
    """Best-effort lineage fold: writes lineage.json and, when codex_knowledge's
    GraphLayer is importable, upserts session->file mutation triples."""
    sid = H.session_id(payload)
    lineage = {
        "session_id": sid,
        "workspace": ws,
        "ts": time.time(),
        "mutations": [str(ev.get("file")) for ev in events if str(ev.get("tool") or "") in H.MUTATION_TOOLS and ev.get("file")],
        "verifications": [str(ev.get("command")) for ev in events if str(ev.get("tool") or "") in H.SHELL_TOOLS and ev.get("verification")],
    }
    H.atomic_json_write(H.root_session_dir(payload) / "lineage.json", lineage)
    if H.is_test_env() and not os.environ.get("CLAUDE_HARNESS_TEST_GRAPH_DB"):
        return
    try:
        src = H.harness_home() / "mcp_servers" / "codex_knowledge" / "src"
        if not src.is_dir():
            return
        if str(src) not in sys.path:
            sys.path.insert(0, str(src))
        from codex_knowledge.graph_layer import GraphLayer  # type: ignore
        from codex_knowledge import settings as ck_settings  # type: ignore
        slug = H.project_slug(ws)
        data_root = Path(getattr(ck_settings, "SETTINGS", ck_settings).data_root) if hasattr(ck_settings, "SETTINGS") else Path(os.path.expanduser("~/.local/share/codex/projects"))
        gdir = data_root / slug / "graph"
        gdir.mkdir(parents=True, exist_ok=True)
        gl = GraphLayer(str(gdir / "graph.sqlite"))
        for f in lineage["mutations"][:30]:
            try:
                gl.upsert("session:%s" % sid[:12], "MUTATED", "file:%s" % os.path.relpath(f, ws), payload=json.dumps({"ts": lineage["ts"]}), layer="episodic", causal_conv_id=sid)
            except Exception:
                continue
    except Exception:
        pass


def maybe_housekeeping(payload: dict) -> None:
    if H.is_test_env():
        return
    try:
        state_file = H.state_dir() / "last_housekeeping.json"
        data = H.atomic_json_read(state_file, default={}) or {}
        last_run = float(data.get("timestamp", 0))
        session_count = int(data.get("session_count", 0)) + 1
        now = time.time()
        sentinel_due = False
        try:
            sentinel = H._load_sentinel()
            if sentinel is not None and hasattr(sentinel, "evaluate_burn_rate"):
                sentinel_due = bool((sentinel.evaluate_burn_rate() or {}).get("escalated"))
        except Exception:
            pass
        if (now - last_run >= 86400) or session_count >= 15 or sentinel_due:
            H.atomic_json_write(state_file, {"timestamp": now, "session_count": 0})
            script = H.scripts_dir() / "housekeeping.py"
            if script.is_file():
                subprocess.Popen([sys.executable, str(script), "--current-conv-id=%s" % H.session_id(payload)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        else:
            H.atomic_json_write(state_file, {"timestamp": last_run, "session_count": session_count})
    except Exception:
        pass


def context_advisory(payload: dict, policy: dict) -> str:
    live = H.live_context_usage(payload)
    try:
        pct = float(live.get("used_percentage") or 0.0)
    except Exception:
        pct = 0.0
    if pct >= float(policy.get("auto_compact_pct", 65.0)) and H.once(payload, "compact_advice", ttl=900):
        return "[Context Health] Context usage is %.0f%% (>= %.0f%%). Recommend `/compact` now; the harness has saved a session snapshot for post-compaction recovery." % (pct, float(policy.get("auto_compact_pct", 65.0)))
    return ""


def spawn_reflector(payload: dict, ws: str) -> None:
    if H.is_test_env():
        return
    try:
        script = H.scripts_dir() / "reflect-experience.py"
        if script.is_file():
            subprocess.Popen(
                [sys.executable, str(script), "--workspace", ws, "--conv-id", H.session_id(payload), "--transcript", str(payload.get("transcript_path") or "")],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
            )
    except Exception:
        pass


def notify(policy: dict, ws: str, n_files: int) -> None:
    if not policy.get("notify") or H.is_test_env():
        return
    try:
        msg = "Modified %d file(s) in %s" % (n_files, os.path.basename(ws))
        if sys.platform == "darwin":
            subprocess.run(["osascript", "-e", 'display notification "%s" with title "Claude Harness: turn complete"' % msg.replace('"', "'")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2, check=False)
        elif H.which("notify-send"):
            subprocess.run(["notify-send", "-a", "Claude Code", "-u", "low", "Claude Harness: turn complete", msg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1, check=False)
    except Exception:
        pass


def decide(payload: dict) -> Optional[dict]:
    ws = H.workspace(payload)
    policy = H.guardrail_policy(ws)
    is_sub = H.is_subagent(payload)
    events = H.iter_events(payload, tail=2000, scoped=False)
    summary = analyze_events(events)
    modified = set(summary["modified"])
    block_reason = ""
    stop_active = bool(payload.get("stop_hook_active"))

    if not is_sub:
        plan = find_unverified_plan(ws, modified)
        if plan and not H.flag_set(payload, "gate_oracle_plan"):
            H.flag_touch(payload, "gate_oracle_plan")
            has_sh = os.path.isfile(os.path.join(ws, "scripts/verification/verify-oracle.sh"))
            directive = "run `bash scripts/verification/verify-oracle.sh --plan` within this turn and " if has_sh else "run an independent `oracle-review` subagent (or /oracle-review) on the plan and "
            block_reason = (
                "[Autonomous Oracle Plan Gate Alert] You created or modified `%s` without completing the Oracle Hardening section. "
                "In Planning Mode you MUST %sappend the Oracle critique, directives, and sign-off under "
                "`## Oracle Hardening, Directives & Verification Matrix` before requesting user approval or proceeding to execution." % (plan.name, directive)
            )
            H.record_harness_failure(payload, "gate_block", block_reason, severity_tier="S1_critical", vertex="skill")

        if not block_reason and len(modified) >= int(policy.get("teardown_file_threshold", 4)) and not (summary["status_updated"] or summary["memory_stored"]) and not H.flag_set(payload, "gate_teardown"):
            H.flag_touch(payload, "gate_teardown")
            block_reason = (
                "[Teardown Gate Alert] This session modified %d files without updating `docs/STATUS.md` or recording knowledge via `codex_knowledge:memory_store`. "
                "Update `docs/STATUS.md` (or the project SOT doc) before final shutdown. Only store memory for non-confounded (verdict: helped) lessons." % len(modified)
            )
            H.record_harness_failure(payload, "gate_block", block_reason, severity_tier="S2_major", vertex="skill")

        if not block_reason and summary["app_code"]:
            if not summary["verified_after_last_edit"] and not H.flag_set(payload, "gate_verify"):
                H.flag_touch(payload, "gate_verify")
                files = ", ".join(sorted(os.path.relpath(f, ws) if f.startswith(ws) else f for f in summary["app_code"]))
                if len(files) > 200:
                    files = files[:197] + "..."
                block_reason = (
                    "[Verification Gate Alert] Causal Past LTL Invariant: application code was modified (%s) without a subsequent verification command "
                    "(or test-runner / oracle subagent) after the last code edit. Execute targeted verification (tests, typecheck, py_compile, or run-compiled-qc.py) before completing." % files
                )
                H.record_harness_failure(payload, "gate_block", block_reason, severity_tier="S1_critical", vertex="skill")
            elif summary["verified_after_last_edit"] and summary["last_verification_failed"] and not H.flag_set(payload, "gate_antibluff"):
                H.flag_touch(payload, "gate_antibluff")
                block_reason = "Anti-Bluffing LTL Gate: the last verification command after your code edit exited with a non-zero status. Fix the failure and re-run verification before concluding."
                H.record_harness_failure(payload, "gate_block", block_reason, severity_tier="S1_critical", vertex="skill")

        if not block_reason and modified and not H.flag_set(payload, "gate_simplify"):
            adv = check_simplify_gate(ws, list(modified), policy)
            if adv:
                H.flag_touch(payload, "gate_simplify")
                block_reason = adv
                H.record_harness_failure(payload, "gate_block", adv, severity_tier="S2_major", vertex="skill")

    # clear satisfied flags so the gate can fire again later in the session
    if not block_reason:
        if summary["status_updated"] or summary["memory_stored"]:
            H.flag_clear(payload, "gate_teardown")
        if summary["verified_after_last_edit"] and not summary["last_verification_failed"]:
            H.flag_clear(payload, "gate_verify")
            H.flag_clear(payload, "gate_antibluff")

    if block_reason and not (stop_active and H.flag_set(payload, "stop_blocked_once")):
        H.flag_touch(payload, "stop_blocked_once")
        return H.block_output(block_reason)

    # Teardown
    write_observation_buffer(payload, events)
    save_session_snapshot(payload, ws, events)
    fold_lineage(payload, ws, events)
    harvest_failures(payload)
    if not is_sub:
        maybe_housekeeping(payload)
        if modified:
            spawn_reflector(payload, ws)
            notify(policy, ws, len(modified))
    H.flag_clear(payload, "stop_blocked_once")
    advisory = context_advisory(payload, policy)
    if advisory:
        return {"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": advisory}, "systemMessage": advisory}
    return None


def main() -> None:
    try:
        payload = H.read_payload()
        if not payload:
            return
        out = decide(payload)
        if out:
            H.emit(out)
    except Exception:
        pass


if __name__ == "__main__":
    main()
