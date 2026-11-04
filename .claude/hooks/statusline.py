#!/usr/bin/env python3
"""Claude Code status line for the SOTA Harness.

Renders a compact one-line status (model | dir | branch | context gauge |
cost | harness gate state) and mirrors the context-window telemetry into
``live_state.json`` so the hooks can compute the 55% / 65% / 75% context-health
alerts (the Antigravity ``agy-statusline`` -> ``antigravity_live_state.json``
pattern).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as H  # noqa: E402

RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"


def gauge(pct: float, width: int = 10) -> str:
    filled = int(round(max(0.0, min(100.0, pct)) / 100.0 * width))
    color = GREEN if pct < 55 else (YELLOW if pct < 75 else RED)
    return "%s%s%s%s" % (color, "█" * filled, "░" * (width - filled), RESET)


def git_branch(cwd: str) -> str:
    try:
        res = subprocess.run(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, timeout=0.5, check=False)
        return res.stdout.strip() if res.returncode == 0 else ""
    except Exception:
        return ""


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}
    model = (data.get("model") or {}).get("display_name") or (data.get("model") or {}).get("id") or "claude"
    ws = (data.get("workspace") or {}).get("current_dir") or data.get("cwd") or os.getcwd()
    ctx = data.get("context_window") or {}
    pct = ctx.get("used_percentage")
    try:
        pct_f = float(pct) if pct is not None else 0.0
    except Exception:
        pct_f = 0.0
    cost = (data.get("cost") or {}).get("total_cost_usd")
    sid = data.get("session_id") or ""

    # mirror telemetry for hooks
    try:
        H.atomic_json_write(H.live_state_path(), {
            "session_id": sid,
            "ts": time.time(),
            "model": model,
            "used_percentage": pct_f,
            "context_window_size": ctx.get("context_window_size"),
            "current_usage": ctx.get("current_usage"),
            "total_input_tokens": ctx.get("total_input_tokens"),
            "total_output_tokens": ctx.get("total_output_tokens"),
            "cost_usd": cost,
            "cwd": ws,
        })
    except Exception:
        pass

    gates = []
    try:
        payload = {"session_id": sid, "cwd": ws}
        flags_dir = H.session_dir(payload, scoped=False) / "flags"
        if (flags_dir / "gate_verify").is_file():
            gates.append("verify!")
        if (flags_dir / "gate_oracle_plan").is_file():
            gates.append("oracle!")
        pending = H.load_state(payload, "syntax_pending", default=None, scoped=False)
        if isinstance(pending, dict):
            gates.append("syntax!")
    except Exception:
        pass

    branch = git_branch(ws)
    parts = [
        "%s%s%s" % (BOLD, model, RESET),
        "%s%s%s" % (CYAN, os.path.basename(ws.rstrip("/")) or ws, RESET),
    ]
    if branch:
        parts.append("%s⎇ %s%s" % (DIM, branch, RESET))
    parts.append("ctx %s %3.0f%%" % (gauge(pct_f), pct_f))
    if isinstance(cost, (int, float)):
        parts.append("%s$%.2f%s" % (DIM, cost, RESET))
    if gates:
        parts.append("%s%s%s" % (RED, " ".join(gates), RESET))
    parts.append("%sharness v%s%s" % (DIM, H.HARNESS_VERSION, RESET))
    sys.stdout.write(" │ ".join(parts))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
