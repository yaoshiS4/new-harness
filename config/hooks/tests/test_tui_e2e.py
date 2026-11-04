"""End-to-End Test Suite for Antigravity TUI State & CLI Architecture.

Validates:
1. test_new_session_resets_context_and_cache_e2e (Directive 1, 2, 3: zero cross-session bleed,
   honest transcript fallback, no mcp_config mutation, W-07 compliance in statusline & sidebar).
2. test_multi_session_tmux_isolation (Directive 1: strict per-session partitioning under tmux).
3. test_subagent_role_mapping_by_conversation_id (Directive 3 / B-13: key roles by conversationId).
4. test_agy_squad_invariants_and_mermaid_cli (Directive 4 / B-08, B-09, B-12: STATE-04 lock inode,
   agy_tui_core.set_sidebar_mode, clean palette, Unicode box-drawing diagram rendering).
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

# Resolve local repository paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

candidate_lib_dirs = [
    os.path.join(REPO_ROOT, "lib"),
    os.path.expanduser("~/.local/lib"),
]
for ld in reversed(candidate_lib_dirs):
    if os.path.isdir(ld) and ld not in sys.path:
        sys.path.insert(0, ld)

candidate_bin_dirs = [
    os.path.join(REPO_ROOT, "bin"),
    os.path.expanduser("~/.local/bin"),
]
BIN_DIR = next((bd for bd in candidate_bin_dirs if os.path.isdir(bd)), os.path.join(REPO_ROOT, "bin"))
LIB_DIR = next((ld for ld in candidate_lib_dirs if os.path.isdir(ld)), os.path.join(REPO_ROOT, "lib"))

import agy_tui_core


class TestTuiEndToEnd(unittest.TestCase):
    """Real subprocess and state-machine E2E test suite for Antigravity TUI."""

    def test_new_session_resets_context_and_cache_e2e(self) -> None:
        """Verifies session reset clears telemetry, prevents old cache/token bleed, preserves config, and respects W-07."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, ".cache")
            os.makedirs(cache_dir, exist_ok=True)
            live_state_path = os.path.join(cache_dir, "antigravity_live_state.json")

            brain_dir = os.path.join(tmpdir, ".gemini", "antigravity-cli", "brain")
            prev_cid = "prev-session-1234"
            prev_log_dir = os.path.join(brain_dir, prev_cid, ".system_generated", "logs")
            os.makedirs(prev_log_dir, exist_ok=True)

            config_dir = os.path.join(tmpdir, ".gemini", "config")
            os.makedirs(config_dir, exist_ok=True)
            mcp_config_path = os.path.join(config_dir, "mcp_config.json")

            # 1. Seed LIVE_STATE_PATH with previous session having high token/cache usage
            seed_data = {
                "ts": time.time() - 300,
                "conversation_id": prev_cid,
                "context_window": {
                    "used_percentage": 74.2,
                    "total_input_tokens": 520000,
                    "total_output_tokens": 42000,
                    "context_window_size": 1048576,
                    "exceeds_200k_tokens": True,
                },
                "cache_hit_pct": 94,
                "ctx_history": [20, 50, 74],
                "vel_history": [1200, 1800],
                "tok_per_min": 1800,
                "workspace": {"current_dir": "/prev/ws"},
                "model": {"display_name": "Gemini 4 Argon", "id": "gemini-4-argon"},
                "subagents": [],
            }
            with open(live_state_path, "w", encoding="utf-8") as f:
                json.dump(seed_data, f)

            # 2. Create fake transcript.jsonl under prev_cid with large step contents
            tr_file = os.path.join(prev_log_dir, "transcript.jsonl")
            with open(tr_file, "w", encoding="utf-8") as f:
                for idx in range(1, 10):
                    f.write(json.dumps({
                        "step_index": idx,
                        "type": "USER_INPUT" if idx == 1 else "PLANNER_RESPONSE",
                        "status": "DONE",
                        "input_tokens": 50000 * idx,
                        "cache_read_tokens": 47000 * idx,
                        "output_tokens": 4000 * idx,
                        "content": f"Large content payload for step {idx}",
                    }) + "\n")

            # 3. Seed mcp_config.json
            initial_mcp_config = {
                "mcpServers": {
                    "browseros-neo": {"serverUrl": "http://127.0.0.1:9010/mcp"}
                },
                "disabledMcpServers": {}
            }
            with open(mcp_config_path, "w", encoding="utf-8") as f:
                json.dump(initial_mcp_config, f, indent=2)

            # Seed deterministic quota cache to ensure hermetic test execution without live API calls
            seeded_quota = {
                "ts": time.time(),
                "quota": {
                    "gemini-weekly": {"remaining_fraction": 0.85, "remaining_amount": None, "reset_time": "2026-10-31T00:00:00Z", "window": "weekly"},
                    "gemini-5h": {"remaining_fraction": 0.85, "remaining_amount": None, "reset_time": "2026-10-27T18:00:00Z", "window": "5h"},
                    "3p-weekly": {"remaining_fraction": 1.0, "remaining_amount": None, "reset_time": "2026-11-03T00:00:00Z", "window": "weekly"},
                    "3p-5h": {"remaining_fraction": 1.0, "remaining_amount": None, "reset_time": "2026-10-27T18:00:00Z", "window": "5h"},
                },
            }
            for q_path in (
                os.path.join(tmpdir, ".gemini", "antigravity-cli", "quota_cache.json"),
                os.path.join(tmpdir, ".cache", "antigravity_quota.json"),
                os.path.join(tmpdir, ".cache", "antigravity_quota_cache.json"),
            ):
                os.makedirs(os.path.dirname(q_path), exist_ok=True)
                with open(q_path, "w", encoding="utf-8") as f:
                    json.dump(seeded_quota, f)

            env = os.environ.copy()
            env.pop("TMUX", None)
            env.pop("TMUX_PANE", None)
            env["HOME"] = tmpdir
            env["PYTHONPATH"] = f"{LIB_DIR}:{env.get('PYTHONPATH', '')}"

            new_ws_dir = os.path.join(tmpdir, "workspaces", "new_project")
            os.makedirs(new_ws_dir, exist_ok=True)

            sidebar_script = os.path.join(BIN_DIR, "agy-sidebar")
            statusline_script = os.path.join(BIN_DIR, "agy-statusline")

            # 4a. DIRECT STATUSLINE INVOCATION WITHOUT RESET:
            # When LIVE_STATE_PATH on disk still holds a previous session (74.2% context, 94% cache),
            # agy-statusline MUST NOT copy or leak old session's context/cache onto the fresh session.
            fresh_stdin = json.dumps({
                "workspace": {"current_dir": new_ws_dir},
                "model": {"display_name": "Gemini 4 Argon"},
            })

            proc_direct_status = subprocess.run(
                [sys.executable, statusline_script],
                input=fresh_stdin,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc_direct_status.returncode, 0, f"Direct statusline failed: {proc_direct_status.stderr}")
            direct_stdout = proc_direct_status.stdout
            self.assertNotIn("94%", direct_stdout, "Direct statusline must NOT leak previous session's 94% cache hit")
            self.assertNotIn("74%", direct_stdout, "Direct statusline must NOT leak previous session's 74% context")
            self.assertNotIn("74.2%", direct_stdout, "Direct statusline must NOT leak previous session's 74.2% context")
            for w07_prefix in ("Cache:", "Ctx:", "In:", "Out:"):
                self.assertNotIn(w07_prefix, direct_stdout, f"Statusline output contains W-07 prefix '{w07_prefix}'")

            # 4b. Invoke agy-sidebar --reset-state <new_ws_dir>
            proc_reset = subprocess.run(
                [sys.executable, sidebar_script, "--reset-state", new_ws_dir],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc_reset.returncode, 0, f"Reset state exited with error: {proc_reset.stderr}")

            # 5. Verify LIVE_STATE_PATH has all telemetry reset cleanly
            with open(live_state_path, "r", encoding="utf-8") as f:
                reset_state = json.load(f)

            self.assertEqual(reset_state.get("conversation_id"), "")
            self.assertEqual(reset_state.get("cache_hit_pct"), 0)
            ctx = reset_state.get("context_window", {})
            self.assertEqual(ctx.get("used_percentage"), 0.0)
            self.assertEqual(ctx.get("total_input_tokens"), 0)
            self.assertEqual(reset_state.get("ctx_history"), [])
            self.assertEqual(reset_state.get("vel_history"), [])
            self.assertEqual(reset_state.get("tok_per_min"), 0)

            # 6. Verify ~/.gemini/config/mcp_config.json was NOT mutated
            with open(mcp_config_path, "r", encoding="utf-8") as f:
                post_reset_mcp = json.load(f)
            self.assertEqual(post_reset_mcp, initial_mcp_config, "reset_live_state must not mutate mcp_config.json")

            # 7. Invoke agy-statusline with a fresh session (0 tokens, no conv_id, TMUX_PANE=%1)
            fresh_stdin = json.dumps({
                "workspace": {"current_dir": new_ws_dir},
                "model": {"display_name": "Gemini 4 Argon"},
            })
            env_statusline = env.copy()
            env_statusline["TMUX_PANE"] = "%1"

            # Refresh sidebar_check_ts right before statusline execution to ensure active sidebar TTL is valid
            reset_state["sidebar_check_ts"] = time.time()
            with open(live_state_path, "w", encoding="utf-8") as f:
                json.dump(reset_state, f)

            proc_status = subprocess.run(
                [sys.executable, statusline_script],
                input=fresh_stdin,
                env=env_statusline,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc_status.returncode, 0, f"agy-statusline failed: {proc_status.stderr}")

            # 8. Check statusline rendered output: does NOT contain 94% or 74%, zero W-07 prefixes
            status_stdout = proc_status.stdout
            self.assertNotIn("94%", status_stdout, "Statusline must not leak previous session's 94% cache hit")
            self.assertNotIn("74%", status_stdout, "Statusline must not leak previous session's 74% context")
            for w07_prefix in ("Cache:", "Ctx:", "In:", "Out:"):
                self.assertNotIn(w07_prefix, status_stdout, f"Statusline output contains W-07 prefix '{w07_prefix}'")
            self.assertIn("↑0", status_stdout, "Statusline should show 0 input tokens")
            self.assertIn("↓0", status_stdout, "Statusline should show 0 output tokens")

            # Check statusline in standalone/hidden sidebar mode: shows 0% context gauge cleanly
            reset_state["sidebar_hidden"] = True
            with open(live_state_path, "w", encoding="utf-8") as f:
                json.dump(reset_state, f)

            proc_status_hidden = subprocess.run(
                [sys.executable, statusline_script],
                input=fresh_stdin,
                env=env_statusline,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc_status_hidden.returncode, 0)
            status_hidden_stdout = proc_status_hidden.stdout
            self.assertIn("0%", status_hidden_stdout, "Standalone statusline should display 0% context")
            self.assertNotIn("94%", status_hidden_stdout)
            self.assertNotIn("74%", status_hidden_stdout)
            for w07_prefix in ("Cache:", "Ctx:", "In:", "Out:"):
                self.assertNotIn(w07_prefix, status_hidden_stdout)

            # 9. Verify resolve_session_token_telemetry, render_sidebar, and render_rail on reset state
            old_home = os.environ.get("HOME")
            os.environ["HOME"] = tmpdir
            try:
                sidebar_mod = runpy.run_path(sidebar_script, run_name="test_sidebar_mod")
                resolve_fn = sidebar_mod.get("resolve_session_token_telemetry") or getattr(agy_tui_core, "resolve_session_token_telemetry", None)
                render_fn = sidebar_mod.get("render_sidebar")
                render_rail_fn = sidebar_mod.get("render_rail")

                self.assertIsNotNone(resolve_fn, "resolve_session_token_telemetry must exist in agy-sidebar")
                self.assertIsNotNone(render_fn, "render_sidebar must exist in agy-sidebar")
                self.assertIsNotNone(render_rail_fn, "render_rail must exist in agy-sidebar")

                in_tok, out_tok, used_pct, cache_hit = resolve_fn(reset_state, root_cid="")
                self.assertEqual(in_tok, 0, "in_tok must be 0 for reset session")
                self.assertEqual(out_tok, 0, "out_tok must be 0 for reset session")
                self.assertEqual(used_pct, 0.0, "used_pct must be 0.0 for reset session")
                self.assertEqual(cache_hit, 0, "cache_hit must be 0 for reset session")

                rendered_sidebar_lines = render_fn(40, 50, state=reset_state)
                rendered_text = "\n".join(rendered_sidebar_lines)
                self.assertNotIn("74%", rendered_text, "render_sidebar must not fabricate tokens from old transcripts")
                self.assertNotIn("94%", rendered_text, "render_sidebar must not fabricate cache hit from old transcripts")
                for w07_label in ("Model  ", "Mode   ", "Ctx    ", "Tokens "):
                    self.assertNotIn(w07_label, rendered_text, f"Sidebar contains W-07 label '{w07_label}'")

                # Verify render_rail does not fabricate tokens or cache from old transcripts
                rendered_rail_lines = render_rail_fn(8, 40)
                rail_text = "\n".join(rendered_rail_lines)
                self.assertNotIn("74%", rail_text, "render_rail must not fabricate tokens from old transcripts")
                self.assertNotIn("94%", rail_text, "render_rail must not fabricate cache hit from old transcripts")
            finally:
                if old_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = old_home

    def test_multi_session_tmux_isolation(self) -> None:
        """Verifies multi-session tmux isolation under Directive 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, ".cache")
            os.makedirs(cache_dir, exist_ok=True)
            live_state_path = os.path.join(cache_dir, "antigravity_live_state.json")

            # Seed sess-a with 65% context and 88% cache hit
            initial_state = {
                "sessions": {
                    "sess-a": {
                        "conversation_id": "conv-a",
                        "context_window": {
                            "used_percentage": 65.0,
                            "total_input_tokens": 120000,
                            "total_output_tokens": 15000,
                            "context_window_size": 1048576,
                        },
                        "cache_hit_pct": 88,
                        "workspace": {"current_dir": "/ws/a"},
                        "model": {"display_name": "Gemini 4 Argon"},
                    }
                }
            }
            with open(live_state_path, "w", encoding="utf-8") as f:
                json.dump(initial_state, f)

            env = os.environ.copy()
            env.pop("TMUX", None)
            env["HOME"] = tmpdir
            env["PYTHONPATH"] = f"{LIB_DIR}:{env.get('PYTHONPATH', '')}"
            env["TMUX_PANE"] = "sess-b"

            sidebar_script = os.path.join(BIN_DIR, "agy-sidebar")

            # Reset sess-b
            proc = subprocess.run(
                [sys.executable, sidebar_script, "--reset-state", "/ws/b"],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, f"Reset sess-b failed: {proc.stderr}")

            # Verify read_live_state(session_key="sess-a") vs read_live_state(session_key="sess-b")
            old_home = os.environ.get("HOME")
            os.environ["HOME"] = tmpdir
            orig_live_state_path = agy_tui_core.LIVE_STATE_PATH
            try:
                agy_tui_core.LIVE_STATE_PATH = live_state_path

                state_a = agy_tui_core.read_live_state(session_key="sess-a")
                self.assertEqual(state_a.get("cache_hit_pct"), 88, "sess-a cache_hit_pct must be retained")
                ctx_a = state_a.get("context_window", {})
                self.assertEqual(ctx_a.get("used_percentage"), 65.0, "sess-a context used_percentage must be 65.0")

                state_b = agy_tui_core.read_live_state(session_key="sess-b")
                self.assertEqual(state_b.get("cache_hit_pct"), 0, "sess-b cache_hit_pct must be 0 after reset")
                ctx_b = state_b.get("context_window", {})
                self.assertEqual(ctx_b.get("used_percentage"), 0.0, "sess-b context used_percentage must be 0.0")
            finally:
                agy_tui_core.LIVE_STATE_PATH = orig_live_state_path
                if old_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = old_home

    def test_subagent_role_mapping_by_conversation_id(self) -> None:
        """Verifies subagent transcript role resolution matches by conversationId rather than index position."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain_dir = os.path.join(tmpdir, ".gemini", "antigravity-cli", "brain")
            root_cid = "root-subagent-test"
            log_dir = os.path.join(brain_dir, root_cid, ".system_generated", "logs")
            os.makedirs(log_dir, exist_ok=True)

            tr_path = os.path.join(log_dir, "transcript.jsonl")
            with open(tr_path, "w", encoding="utf-8") as f:
                # Step 1: invokes subagent with Role frontend-explorer
                f.write(json.dumps({
                    "step_index": 1,
                    "type": "PLANNER_RESPONSE",
                    "tool_calls": [{
                        "name": "invoke_subagent",
                        "args": {"Role": "frontend-explorer", "TypeName": "research"}
                    }]
                }) + "\n")
                # Step 2: tool response returns conversationId id-1
                f.write(json.dumps({
                    "step_index": 2,
                    "type": "GENERIC",
                    "content": json.dumps({"conversationId": "id-1"})
                }) + "\n")
                # Step 3: invokes subagent with Role oracle-review
                f.write(json.dumps({
                    "step_index": 3,
                    "type": "PLANNER_RESPONSE",
                    "tool_calls": [{
                        "name": "invoke_subagent",
                        "args": {"Role": "oracle-review", "TypeName": "self"}
                    }]
                }) + "\n")
                # Step 4: tool response returns conversationId id-2
                f.write(json.dumps({
                    "step_index": 4,
                    "type": "GENERIC",
                    "content": json.dumps({"conversationId": "id-2"})
                }) + "\n")

            sidebar_script = os.path.join(BIN_DIR, "agy-sidebar")
            orig_brain_dir = agy_tui_core.BRAIN_DIR
            try:
                agy_tui_core.BRAIN_DIR = brain_dir
                sidebar_mod = runpy.run_path(sidebar_script, run_name="test_sidebar_mod")
                resolve_roles_fn = sidebar_mod.get("get_subagent_roles_from_transcript")
                self.assertIsNotNone(resolve_roles_fn, "get_subagent_roles_from_transcript must exist")

                roles = resolve_roles_fn(root_cid)
                self.assertIsInstance(roles, dict, "get_subagent_roles_from_transcript must return dict keyed by conversationId")
                self.assertEqual(roles.get("id-1"), "frontend-explorer", "id-1 must map strictly to frontend-explorer")
                self.assertEqual(roles.get("id-2"), "oracle-review", "id-2 must map strictly to oracle-review")

                # Test reverse-order subagent list mapping (id-2 before id-1)
                all_subs = [
                    {"id": "id-2", "conversationId": "id-2", "role": "self", "status": "running"},
                    {"id": "id-1", "conversationId": "id-1", "role": "research", "status": "running"},
                ]
                for s in all_subs:
                    cid = s.get("conversationId") or s.get("id")
                    if cid in roles:
                        s["role"] = roles[cid]
                self.assertEqual(all_subs[0]["role"], "oracle-review", "Out-of-order id-2 must strictly map to oracle-review")
                self.assertEqual(all_subs[1]["role"], "frontend-explorer", "Out-of-order id-1 must strictly map to frontend-explorer")
            finally:
                agy_tui_core.BRAIN_DIR = orig_brain_dir

    def test_agy_squad_invariants_and_mermaid_cli(self) -> None:
        """Verifies agy-squad uses agy_tui_core, preserves popup lockfile inode, has clean palette, and mermaid renders Unicode boxes."""
        squad_script = os.path.join(BIN_DIR, "agy-squad")
        with open(squad_script, "r", encoding="utf-8") as f:
            squad_src = f.read()

        # 1. Verify agy-squad imports and uses agy_tui_core.set_sidebar_mode, resolve_workspace_cwd, and connect_db_ro
        self.assertIn("set_sidebar_mode", squad_src)
        self.assertNotIn("def set_sidebar_mode(", squad_src, "agy-squad must not define a local unflocked set_sidebar_mode")
        self.assertNotIn("def resolve_workspace_cwd(", squad_src, "agy-squad must not define a local resolve_workspace_cwd duplicate")
        self.assertIn("resolve_workspace_cwd", squad_src, "agy-squad must import resolve_workspace_cwd from agy_tui_core")
        self.assertNotIn("sqlite3.connect(", squad_src, "agy-squad must use connect_db_ro context manager instead of raw sqlite3.connect")
        self.assertIn("connect_db_ro", squad_src, "agy-squad must import connect_db_ro from agy_tui_core")

        # 2. Verify STATE-04 lock inode preservation: os.remove(POPUP_LOCK_FILE) must be absent
        self.assertNotIn("os.remove(POPUP_LOCK_FILE)", squad_src, "POPUP_LOCK_FILE must never be unlinked on unlock")
        self.assertNotIn("os.remove(lock_file)", squad_src, "lock_file must never be unlinked on unlock")

        # Simulate lockfile inode preservation across flock release
        with tempfile.TemporaryDirectory() as tmpdir:
            test_lock = os.path.join(tmpdir, "test_popup.lock")
            with open(test_lock, "w") as f:
                f.write("test:1234")
            initial_inode = os.stat(test_lock).st_ino

            # Acquire lock
            fd = open(test_lock, "w")
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Release lock without unlinking
            fcntl.flock(fd, fcntl.LOCK_UN)
            fd.close()

            self.assertTrue(os.path.exists(test_lock), "Lock file must remain on disk after unlock")
            self.assertEqual(os.stat(test_lock).st_ino, initial_inode, "Lock file inode must be preserved")

        # 3. Verify Command Palette has no "KQ " garbage and specifies 8-col width
        proc_pal = subprocess.run(
            [sys.executable, squad_script, "--command-palette", "--dump"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_pal.returncode, 0, f"Command palette dump failed: {proc_pal.stderr}")
        self.assertNotIn("KQ ", proc_pal.stdout, "Command palette must not contain 'KQ ' prefix")
        self.assertIn("8-col", proc_pal.stdout, "Compact Rail Sidebar must be 8-col width")

        # 4. Verify bin/mermaid-ascii renders diagrams into Unicode box-drawing characters
        mermaid_bin = os.path.join(BIN_DIR, "mermaid-ascii")
        mermaid_input = "graph TD\nA[\"Start\"] --> B[\"End\"]\n"
        proc_mermaid = subprocess.run(
            [sys.executable, mermaid_bin],
            input=mermaid_input,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc_mermaid.returncode, 0, f"mermaid-ascii failed: {proc_mermaid.stderr}")
        diagram = proc_mermaid.stdout
        self.assertIn("Start", diagram)
        self.assertIn("End", diagram)
        # Check Unicode box-drawing characters
        for char in ("╭", "╰", "─", "│"):
            self.assertIn(char, diagram, f"Mermaid diagram must contain Unicode box-drawing character '{char}'")

        # 5. Verify tmux codepoint-widths and agy_tui_core.char_cell_width for U+FFF9..U+FFFB
        tmux_conf_path = os.path.join(REPO_ROOT, "config", "tui", ".tmux.conf")
        with open(tmux_conf_path, "r", encoding="utf-8") as f:
            tmux_conf_src = f.read()
        self.assertIn('codepoint-widths[0] "U+FFF9-U+FFFB=0"', tmux_conf_src, "config/tui/.tmux.conf must configure U+FFF9-U+FFFB=0")
        self.assertIn('codepoint-widths[1] "U+00AD=0"', tmux_conf_src, "config/tui/.tmux.conf must configure U+00AD=0")

        # Verify char_cell_width classifies format control chars U+FFF9..U+FFFB as zero-width (0 cells)
        for cf_char in ("\ufff9", "\ufffa", "\ufffb"):
            self.assertEqual(agy_tui_core.char_cell_width(cf_char), 0, f"char_cell_width('{hex(ord(cf_char))}') must be 0")
        self.assertEqual(agy_tui_core.char_cell_width("\u00ad"), 0, "char_cell_width for soft hyphen U+00AD must be 0")
        self.assertEqual(agy_tui_core.char_cell_width("\ufeff"), 0, "char_cell_width for BOM U+FEFF must be 0")

    def test_stale_sessions_pruning_and_entry_cap(self) -> None:
        """Verifies agy-statusline evicts expired (>24h) and dead-PID sessions and caps retained entries to 32."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, ".cache")
            os.makedirs(cache_dir, exist_ok=True)
            live_state_path = os.path.join(cache_dir, "antigravity_live_state.json")

            now = time.time()
            seeded_sessions: dict[str, dict] = {}

            # 15 expired entries (>24h old)
            for i in range(15):
                seeded_sessions[f"%old-{i}"] = {
                    "conversation_id": f"expired-{i}",
                    "updated_at": now - 90000.0 - i,
                }

            # Dead Linux agy-<pid> entry older than 600s
            seeded_sessions["agy-99999999"] = {
                "conversation_id": "dead-pid-conv",
                "updated_at": now - 750.0,
            }

            # 38 recent entries within the last few minutes (exceeding 32-entry cap)
            for i in range(38):
                seeded_sessions[f"%recent-{i:02d}"] = {
                    "conversation_id": f"recent-conv-{i:02d}",
                    "updated_at": now - (i * 5.0),
                }

            with open(live_state_path, "w", encoding="utf-8") as f:
                json.dump({"sessions": seeded_sessions}, f)

            seeded_quota = {
                "ts": now,
                "quota": {
                    "gemini-weekly": {"remaining_fraction": 0.9, "remaining_amount": None, "reset_time": "2026-11-10T00:00:00Z", "window": "weekly"},
                    "gemini-5h": {"remaining_fraction": 0.9, "remaining_amount": None, "reset_time": "2026-11-02T00:00:00Z", "window": "5h"},
                },
            }
            for q_path in (
                os.path.join(tmpdir, ".gemini", "antigravity-cli", "quota_cache.json"),
                os.path.join(tmpdir, ".cache", "antigravity_quota.json"),
                os.path.join(tmpdir, ".cache", "antigravity_quota_cache.json"),
            ):
                os.makedirs(os.path.dirname(q_path), exist_ok=True)
                with open(q_path, "w", encoding="utf-8") as f:
                    json.dump(seeded_quota, f)

            ws_dir = os.path.join(tmpdir, "ws")
            os.makedirs(ws_dir, exist_ok=True)
            env = os.environ.copy()
            env.pop("TMUX", None)
            env["HOME"] = tmpdir
            env["PYTHONPATH"] = f"{LIB_DIR}:{env.get('PYTHONPATH', '')}"
            env["TMUX_PANE"] = "%active-pane"

            statusline_script = os.path.join(BIN_DIR, "agy-statusline")
            stdin_payload = json.dumps({
                "conversation_id": "active-conv-id",
                "workspace": {"current_dir": ws_dir},
                "model": {"display_name": "Gemini 4 Argon"},
            })
            proc = subprocess.run(
                [sys.executable, statusline_script],
                input=stdin_payload,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, f"agy-statusline failed: {proc.stderr}")

            with open(live_state_path, "r", encoding="utf-8") as f:
                persisted = json.load(f)

            retained = persisted.get("sessions", {})
            self.assertLessEqual(len(retained), 32, "Retained sessions must be capped at 32 entries")
            self.assertEqual(len(retained), 32)
            self.assertIn("%active-pane", retained, "Active session key must always be retained")
            for i in range(15):
                self.assertNotIn(f"%old-{i}", retained, "Sessions older than 24h must be evicted")
            if os.path.isdir("/proc") and not os.path.exists("/proc/99999999"):
                self.assertNotIn("agy-99999999", retained, "Dead agy-<pid> older than 600s must be evicted")
            # Oldest of the 38 recent entries (%recent-37) must be evicted in favor of the 31 newest + %active-pane
            self.assertIn("%recent-00", retained)
            self.assertNotIn("%recent-37", retained)

    def test_step1_zero_cache_honesty_and_exact_transcript_fallback(self) -> None:
        """Verifies Step-1 cache_hit_pct=0 honesty on live input and exact PLANNER_RESPONSE token fallback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain_dir = os.path.join(tmpdir, "brain")
            orig_brain_dir = agy_tui_core.BRAIN_DIR
            agy_tui_core._TOKEN_TELEM_CACHE.clear()
            try:
                agy_tui_core.BRAIN_DIR = brain_dir

                # 1. Live Step-1 state with in_tok > 0, used_pct > 0, cache_read_input_tokens == 0
                # must NOT trigger transcript fallback even if a multi-step transcript exists.
                cid_live = "conv-live-step1"
                log_live = os.path.join(brain_dir, cid_live, ".system_generated", "logs")
                os.makedirs(log_live, exist_ok=True)
                with open(os.path.join(log_live, "transcript.jsonl"), "w", encoding="utf-8") as f:
                    for idx in range(1, 6):
                        f.write(json.dumps({
                            "step_index": idx,
                            "type": "USER_INPUT" if idx == 1 else "PLANNER_RESPONSE",
                            "input_tokens": 10000,
                            "cache_read_tokens": 90000,
                            "output_tokens": 1500,
                            "content": "Synthetic multi-step payload",
                        }) + "\n")

                live_step1_state = {
                    "conversation_id": cid_live,
                    "context_window": {
                        "used_percentage": 7.6,
                        "total_input_tokens": 15152,
                        "total_output_tokens": 735,
                        "current_usage": {
                            "input_tokens": 15152,
                            "cache_read_input_tokens": 0,
                        },
                    },
                }
                telem_live = agy_tui_core.resolve_session_token_telemetry(live_step1_state, root_cid=cid_live)
                self.assertEqual(telem_live["in_tokens"], 15152)
                self.assertEqual(telem_live["out_tokens"], 735)
                self.assertAlmostEqual(telem_live["used_pct"], 7.6)
                self.assertEqual(telem_live["cache_hit_pct"], 0, "Step-1 live cache_read=0 must report honest 0% cache hit")

                # 2. Transcript fallback on Step 1 (input_tokens > 0, cache_read_tokens == 0) keeps cache_hit_pct == 0
                cid_fb_step1 = "conv-fb-step1"
                log_fb1 = os.path.join(brain_dir, cid_fb_step1, ".system_generated", "logs")
                os.makedirs(log_fb1, exist_ok=True)
                with open(os.path.join(log_fb1, "transcript.jsonl"), "w", encoding="utf-8") as f:
                    f.write(json.dumps({"step_index": 1, "type": "USER_INPUT", "content": "Hello"}) + "\n")
                    f.write(json.dumps({
                        "step_index": 2,
                        "type": "PLANNER_RESPONSE",
                        "input_tokens": 15152,
                        "cache_read_tokens": 0,
                        "output_tokens": 735,
                        "content": "First planner turn",
                    }) + "\n")

                telem_fb1 = agy_tui_core.resolve_session_token_telemetry({"conversation_id": cid_fb_step1}, root_cid=cid_fb_step1)
                self.assertEqual(telem_fb1["in_tokens"], 15152)
                self.assertEqual(telem_fb1["out_tokens"], 735)
                self.assertEqual(telem_fb1["cache_hit_pct"], 0, "Transcript fallback with cache_read_tokens=0 must report 0%")

                # 3. Transcript fallback on multi-step session computes exact (last_in + last_cache_read) and real cache_hit_pct
                cid_fb_multi = "conv-fb-multi"
                log_fb_multi = os.path.join(brain_dir, cid_fb_multi, ".system_generated", "logs")
                os.makedirs(log_fb_multi, exist_ok=True)
                with open(os.path.join(log_fb_multi, "transcript.jsonl"), "w", encoding="utf-8") as f:
                    f.write(json.dumps({"step_index": 1, "type": "USER_INPUT", "content": "Turn 1"}) + "\n")
                    f.write(json.dumps({
                        "step_index": 2,
                        "type": "PLANNER_RESPONSE",
                        "input_tokens": 15152,
                        "cache_read_tokens": 0,
                        "output_tokens": 735,
                        "content": "Step 1 reply",
                    }) + "\n")
                    f.write(json.dumps({
                        "step_index": 5,
                        "type": "PLANNER_RESPONSE",
                        "input_tokens": 4411,
                        "cache_read_tokens": 15153,
                        "output_tokens": 683,
                        "content": "Step 2 reply",
                    }) + "\n")

                telem_multi = agy_tui_core.resolve_session_token_telemetry({"conversation_id": cid_fb_multi}, root_cid=cid_fb_multi)
                self.assertEqual(telem_multi["in_tokens"], 4411 + 15153)
                self.assertEqual(telem_multi["out_tokens"], 735 + 683)
                self.assertEqual(telem_multi["cache_hit_pct"], round((15153 / (15153 + 4411)) * 100))

                # 4. Protojson Step-1 usage (omitted zero cache_read* and missing used_percentage)
                # on a 2-line Turn-1 transcript must report cache_hit_pct == 0 (never 48) and non-zero used_pct
                cid_proto_step1 = "conv-protojson-step1"
                log_proto = os.path.join(brain_dir, cid_proto_step1, ".system_generated", "logs")
                os.makedirs(log_proto, exist_ok=True)
                with open(os.path.join(log_proto, "transcript.jsonl"), "w", encoding="utf-8") as f:
                    f.write(json.dumps({"step_index": 1, "type": "USER_INPUT", "content": "Hello " * 40}) + "\n")
                    f.write(json.dumps({"step_index": 2, "type": "PLANNER_RESPONSE", "content": "Reply " * 40}) + "\n")

                telem_proto = agy_tui_core.resolve_session_token_telemetry(
                    {"conversation_id": cid_proto_step1, "usage": {"input_tokens": 13953, "output_tokens": 596}},
                    root_cid=cid_proto_step1,
                )
                self.assertEqual(telem_proto["in_tokens"], 13953)
                self.assertEqual(telem_proto["out_tokens"], 596)
                self.assertGreater(telem_proto["used_pct"], 0.0)
                self.assertEqual(telem_proto["cache_hit_pct"], 0, "Protojson Step-1 usage without cache_read* must report 0% cache hit")

                # Also verify live input_tokens with output_tokens == 0 entering transcript fallback does NOT take byte-estimated cache_hit_pct
                cid_proto_streaming = "conv-protojson-streaming"
                log_proto_stream = os.path.join(brain_dir, cid_proto_streaming, ".system_generated", "logs")
                os.makedirs(log_proto_stream, exist_ok=True)
                with open(os.path.join(log_proto_stream, "transcript.jsonl"), "w", encoding="utf-8") as f:
                    f.write(json.dumps({"step_index": 1, "type": "USER_INPUT", "content": "Prompt " * 40}) + "\n")
                    f.write(json.dumps({"step_index": 2, "type": "PLANNER_RESPONSE", "content": "First " * 40}) + "\n")
                    f.write(json.dumps({"step_index": 3, "type": "PLANNER_RESPONSE", "content": "Second " * 40}) + "\n")

                telem_proto_stream = agy_tui_core.resolve_session_token_telemetry(
                    {"conversation_id": cid_proto_streaming, "usage": {"input_tokens": 13953, "output_tokens": 0}},
                    root_cid=cid_proto_streaming,
                )
                self.assertEqual(telem_proto_stream["cache_hit_pct"], 0, "Live in_tok > 0 with cache_read == 0 must never use byte-estimated cache hit")

                # 5. Byte-estimation fallback when token fields are absent/zero:
                # 1-planner-turn transcript (USER_INPUT + PLANNER_RESPONSE) reports cache_hit_pct == 0;
                # multi-planner-turn transcript (planner_steps >= 2) estimates non-zero cache_hit_pct.
                cid_fb_bytes = "conv-fb-bytes"
                log_fb_bytes = os.path.join(brain_dir, cid_fb_bytes, ".system_generated", "logs")
                os.makedirs(log_fb_bytes, exist_ok=True)
                with open(os.path.join(log_fb_bytes, "transcript.jsonl"), "w", encoding="utf-8") as f:
                    f.write(json.dumps({"step_index": 1, "type": "USER_INPUT", "content": "Prompt " * 80}) + "\n")
                    f.write(json.dumps({"step_index": 2, "type": "PLANNER_RESPONSE", "content": "Answer " * 80}) + "\n")

                telem_bytes = agy_tui_core.resolve_session_token_telemetry({"conversation_id": cid_fb_bytes}, root_cid=cid_fb_bytes)
                self.assertGreater(telem_bytes["in_tokens"], 0)
                self.assertGreater(telem_bytes["out_tokens"], 0)
                self.assertGreater(telem_bytes["used_pct"], 0.0)
                self.assertEqual(telem_bytes["cache_hit_pct"], 0, "1-planner-turn byte fallback must report 0% cache hit")

                cid_fb_bytes_multi = "conv-fb-bytes-multi"
                log_fb_bytes_multi = os.path.join(brain_dir, cid_fb_bytes_multi, ".system_generated", "logs")
                os.makedirs(log_fb_bytes_multi, exist_ok=True)
                with open(os.path.join(log_fb_bytes_multi, "transcript.jsonl"), "w", encoding="utf-8") as f:
                    f.write(json.dumps({"step_index": 1, "type": "USER_INPUT", "content": "Prompt " * 80}) + "\n")
                    f.write(json.dumps({"step_index": 2, "type": "PLANNER_RESPONSE", "content": "Answer 1 " * 80}) + "\n")
                    f.write(json.dumps({"step_index": 3, "type": "PLANNER_RESPONSE", "content": "Answer 2 " * 80}) + "\n")

                telem_bytes_multi = agy_tui_core.resolve_session_token_telemetry({"conversation_id": cid_fb_bytes_multi}, root_cid=cid_fb_bytes_multi)
                self.assertGreater(telem_bytes_multi["cache_hit_pct"], 0, "Multi-planner-turn byte fallback must estimate non-zero cache hit")
            finally:
                agy_tui_core._TOKEN_TELEM_CACHE.clear()
                agy_tui_core.BRAIN_DIR = orig_brain_dir


if __name__ == "__main__":
    unittest.main()
