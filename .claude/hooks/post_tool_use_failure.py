#!/usr/bin/env python3
"""PostToolUseFailure hook: records failed tool executions into the session
ledgers so the Stop gate (anti-bluffing) and the error-stagnation breaker see
them, and clears the read ledger entry for failed reads."""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as H  # noqa: E402
import post_tool_use as POST  # noqa: E402


def main() -> None:
    try:
        payload = H.read_payload()
        if not payload:
            return
        tool_name = str(payload.get("tool_name") or "")
        tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
        error = str(payload.get("error") or "")
        if tool_name in H.SHELL_TOOLS:
            cmd = str(tool_input.get("command") or "")
            verification = POST.is_verification_command(cmd, H.workspace(payload))
            H.append_event(payload, {"tool": "Bash", "command": cmd[:500], "verification": verification, "failed": True, "ok": False, "error": error[:300]})
            ledger = H.load_state(payload, "err_sig", default={}) or {}
            sigs = ledger.get("signatures") or []
            lines = [l.strip() for l in error.splitlines() if l.strip()][-5:]
            cleaned = [re.sub(r"\b0x[0-9a-fA-F]+\b", "0x...", l) for l in lines]
            if cleaned:
                sigs.append(hashlib.sha256("\n".join(cleaned).encode("utf-8")).hexdigest())
            ledger["signatures"] = sigs[-6:]
            ledger["last_error"] = error[-1500:]
            H.save_state(payload, "err_sig", ledger)
            fb = POST.extract_structured_feedback(error)
            if fb.get("failures"):
                fb["command"] = cmd
                fb["session_id"] = H.session_id(payload)
                import time
                fb["timestamp"] = time.time()
                H.save_state(payload, "structured_feedback", fb, scoped=False)
        elif tool_name in H.MUTATION_TOOLS or tool_name in H.READ_TOOLS:
            H.append_event(payload, {"tool": tool_name, "file": H.target_file_of(tool_name, tool_input), "ok": False, "error": error[:300]})
        elif tool_name in H.AGENT_TOOLS:
            H.append_event(payload, {"tool": "Agent", "subagent_type": str(tool_input.get("subagent_type") or ""), "ok": False, "error": error[:300]})
    except Exception:
        pass


if __name__ == "__main__":
    main()
