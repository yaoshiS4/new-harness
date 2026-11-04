#!/usr/bin/env python3
"""SubagentStop hook: scope-drift guard + role trajectory contract telemetry.

* Scope drift: files the subagent mutated outside its ``allowed_files`` lease
  (ported from ``_check_subagent_scope_drift``).
* Trajectory contract: read-only roles must not have used mutation tools;
  builder roles are expected to have edited and verified
  (ported from ``_evaluate_role_trajectory_contract``).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as H  # noqa: E402


def evaluate_trajectory(role: str, tool_names: list) -> dict:
    role_norm = (role or "").lower()
    actual = [H.canonical_tool(t) for t in tool_names if t]
    if H.is_readonly_role(role_norm):
        mode = "subset"
        ref = ["read_file", "call_mcp_tool", "grep", "glob", "webfetch", "websearch", "run_command", "todowrite"]
    elif role_norm in H.BUILDER_ROLES:
        mode = "superset"
        ref = ["write_file", "run_command"] if ("write_file" in actual and "edit_file" not in actual) else ["edit_file", "run_command"]
    else:
        mode = "subset"
        ref = list(dict.fromkeys(actual))
    ref_set = set(ref)
    actual_set = set(actual)
    missing = [t for t in ref if t not in actual_set]
    extra = [t for t in dict.fromkeys(actual) if t not in ref_set]
    if mode == "subset":
        # mutation tools are the only true violations for read-only roles
        extra = [t for t in extra if t in ("write_file", "edit_file")]
        matched = not extra
        score = 1.0 if matched else round(len(actual_set & ref_set) / max(1, len(actual_set)), 4)
    else:
        matched = not missing
        score = 1.0 if matched else round(len(actual_set & ref_set) / max(1, len(ref_set)), 4)
    return {"role": role_norm, "matched": matched, "mode": mode, "actual": actual, "reference": ref, "missing_tools": missing, "extra_tools": extra, "score": score}


def main() -> None:
    try:
        payload = H.read_payload()
        if not payload or not H.is_subagent(payload):
            return
        role = H.role_of(payload)
        ws = H.workspace(payload)
        warnings = []

        lease = H.lease_for(payload)
        mutations = H.load_state(payload, "mutations", default=[], scoped=True) or []
        if lease.get("has_allowed_files") and isinstance(mutations, list):
            allowed = list(lease.get("allowed_files") or [])
            for m in mutations:
                norm = os.path.abspath(os.path.realpath(str(m)))
                if norm.lower().endswith((".md", ".txt")):
                    continue
                if not any(H.matches_allowed_file(norm, pat, ws) for pat in allowed):
                    warnings.append("Scope drift: subagent `%s` mutated unleased file `%s` outside allowed_files %s." % (role, os.path.basename(norm), allowed))

        events = H.iter_events(payload, tail=1000, scoped=True)
        tools = [str(e.get("tool") or "") for e in events]
        tp = str(payload.get("agent_transcript_path") or "")
        if not tools and tp and os.path.isfile(tp):
            tools = [u["name"] for u in H.transcript_tool_uses(tp)]
        traj = evaluate_trajectory(role, tools)
        H.save_state(payload, "trajectory", traj, scoped=True)
        if not traj["matched"] and traj["mode"] == "subset" and traj["extra_tools"]:
            warnings.append("Role trajectory contract violation: read-only role `%s` used mutation tools %s." % (role, traj["extra_tools"]))

        if warnings:
            for w in warnings:
                H.record_harness_failure(payload, "scope_drift", w, tool_name="SubagentStop", severity_tier="S2_major", vertex="skill")
            msg = "[Scope Drift Guard] " + " ".join(warnings)
            H.emit({"hookSpecificOutput": {"hookEventName": "SubagentStop", "additionalContext": msg}, "systemMessage": msg[:2000]})
    except Exception:
        pass


if __name__ == "__main__":
    main()
