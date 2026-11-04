#!/usr/bin/env python3
"""SessionStart hook (port of ``pre_invocation_hook.py --session-start``).

* ``startup`` / ``resume`` / ``clear`` / ``fork``: emits the compact
  ``[Session Grounding Anchor]`` (prefix-pin, project slug, SOT docs, memory
  keys, untrusted-customization scan), reaps stale state, and persists a few
  harness env vars via ``CLAUDE_ENV_FILE``.
* ``compact``: marks the session so the next prompt surfaces the
  post-compaction recovery anchor (LOSS-02).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as H  # noqa: E402
import user_prompt_submit as UPS  # noqa: E402


def scan_untrusted_customizations(ws: str) -> list:
    hazards = []
    if not ws or not os.path.isdir(ws):
        return hazards
    for rel in (".agents/hooks.json", ".agent/hooks.json", "_agents/hooks.json", "_agent/hooks.json"):
        if os.path.lexists(os.path.join(ws, rel)):
            hazards.append(rel)
    local = os.path.join(ws, ".claude", "settings.local.json")
    if os.path.isfile(local):
        try:
            data = json.loads(open(local, "r", encoding="utf-8").read())
            if isinstance(data, dict) and data.get("hooks") and os.environ.get("CLAUDE_HARNESS_TRUST_LOCAL_HOOKS") != "1":
                hazards.append(".claude/settings.local.json (hooks)")
        except Exception:
            pass
    return hazards


def prefix_pin(slug: str, role: str, sot: list) -> str:
    canonical = json.dumps({"slug": slug, "role": role, "sot_docs": sorted(sot)}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:8]


def build_anchor(payload: dict, ws: str) -> str:
    slug = H.project_slug(ws)
    sot = H.find_sot_docs(ws)
    role = H.role_of(payload)
    mem = UPS.memory_seeds(slug, "", limit=3)
    installed = (H.claude_home() / "CLAUDE.md").is_file() and "CLAUDE_HARNESS_MANAGED" in (H.claude_home() / "CLAUDE.md").read_text(encoding="utf-8", errors="ignore")
    lines = [
        "[Session Grounding Anchor] (%s)" % slug,
        "- Prefix-Pin: %s | Role: %s | Source: %s" % (prefix_pin(slug, role, sot), role, payload.get("source") or "startup"),
        "- Project Slug: %s | Workspace SOT: %s" % (slug, ", ".join(sot[:3]) if sot else "none"),
        "- Memory Keys: %s" % (", ".join(mem) if mem else "none"),
    ]
    if not installed:
        lines.append("- Harness: global contract not installed in ~/.claude/CLAUDE.md; run `bash scripts/install-claude-harness.sh` for the full runtime (project hooks are active).")
    hazards = scan_untrusted_customizations(ws)
    if hazards:
        lines.append("- [SECURITY ALERT] Untrusted customization in workspace: %s" % ", ".join(hazards))
    anchor = "\n".join(lines)
    return anchor[:597].rstrip() + "..." if len(anchor) > 600 else anchor


def persist_env() -> None:
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file:
        return
    try:
        with open(env_file, "a", encoding="utf-8") as f:
            f.write("export CLAUDE_HARNESS_HOME=%s\n" % json.dumps(str(H.harness_home())))
            f.write("export CLAUDE_HARNESS_STATE_DIR=%s\n" % json.dumps(str(H.state_dir())))
    except Exception:
        pass


def main() -> None:
    try:
        payload = H.read_payload()
        source = str(payload.get("source") or "startup")
        if source == "compact":
            H.flag_touch(payload, "post_compact_pending")
            return
        if H.is_subagent(payload):
            return
        H.reap_stale_state()
        persist_env()
        ws = H.workspace(payload)
        # reset per-session turn counter on fresh starts
        meta = {"turn": 0} if source in ("startup", "clear") else (H.load_state(payload, "session_meta", default={}, scoped=False) or {})
        if payload.get("model"):
            meta["model"] = str(payload.get("model"))
        if payload.get("transcript_path"):
            meta["transcript_path"] = str(payload.get("transcript_path"))
        H.save_state(payload, "session_meta", meta, scoped=False)
        H.emit(H.context_output("SessionStart", build_anchor(payload, ws)))
    except Exception:
        pass


if __name__ == "__main__":
    main()
