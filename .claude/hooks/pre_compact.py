#!/usr/bin/env python3
"""PreCompact hook: persist the LOSS-02 session snapshot and observation buffer
before Claude Code compacts the context, and arm the post-compaction recovery
anchor for the next prompt."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as H  # noqa: E402
import stop as STOP  # noqa: E402


def main() -> None:
    try:
        payload = H.read_payload()
        if not payload:
            return
        ws = H.workspace(payload)
        events = H.iter_events(payload, tail=2000, scoped=False)
        STOP.write_observation_buffer(payload, events)
        STOP.save_session_snapshot(payload, ws, events)
        H.flag_touch(payload, "post_compact_pending")
        H.save_state(payload, "ctx_alert", {}, scoped=False)
    except Exception:
        pass


if __name__ == "__main__":
    main()
