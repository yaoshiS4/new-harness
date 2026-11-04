#!/usr/bin/env python3
"""Wave 4 Shard D1 unit & integration tests: Lifecycle, Latency & Reactive-Stop Harmonization."""
from __future__ import annotations

import io
import json
import os
import runpy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HOOKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO_ROOT = os.path.abspath(os.path.join(HOOKS_DIR, "..", ".."))

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
BIN_DIR = next(
    (bd for bd in candidate_bin_dirs if os.path.isfile(os.path.join(bd, "agy-sidebar"))),
    os.path.join(REPO_ROOT, "bin"),
)
LIB_DIR = next((ld for ld in candidate_lib_dirs if os.path.isdir(ld)), os.path.join(REPO_ROOT, "lib"))

if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

import agy_tui_core  # noqa: E402, F401
import pre_invocation_hook  # noqa: E402
import stop_hook  # noqa: E402


class TestWave4LifecycleD1(unittest.TestCase):
    """Tests for Shard D1: SessionStart anchor, SYSTEM_SDK step-0 skip, Turn 2..N fast-path, fullyIdle Stop, and TUI plugin state."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = self._tmp.name
        self.states_dir = os.path.join(self.tmpdir, "session_states")
        os.makedirs(self.states_dir, exist_ok=True)
        self._env_patch = mock.patch.dict(
            os.environ,
            {"ANTIGRAVITY_SESSION_STATES_DIR": self.states_dir},
            clear=False,
        )
        self._env_patch.start()

    def tearDown(self) -> None:
        self._env_patch.stop()
        self._tmp.cleanup()

    def test_session_start_root_anchor_and_untrusted_scan(self) -> None:
        ws = os.path.join(self.tmpdir, "ws_root")
        os.makedirs(os.path.join(ws, "docs"), exist_ok=True)
        os.makedirs(os.path.join(ws, ".agents", "plugins", "rogue_plugin"), exist_ok=True)
        Path(os.path.join(ws, "AGENTS.md")).write_text("# Agents\n", encoding="utf-8")
        Path(os.path.join(ws, "docs", "STATUS.md")).write_text("# Status\n", encoding="utf-8")
        Path(os.path.join(ws, ".agents", "hooks.json")).write_text("{}", encoding="utf-8")

        conv_id = "root-session-001"
        payload = {
            "conversationId": conv_id,
            "workspacePaths": [ws],
            "modelName": "gemini-4-argon-medium",
        }

        buf = io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["pre_invocation_hook.py", "--session-start"]),
            mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
            mock.patch.object(sys, "stdout", buf),
            mock.patch.object(pre_invocation_hook, "_ensure_cli_statusline_and_yolo_settings") as m_status,
            mock.patch.object(pre_invocation_hook, "_reap_stale_tmp_artifacts") as m_reap,
            mock.patch.object(pre_invocation_hook, "_auto_disable_browseros_mcp") as m_browseros,
            mock.patch.object(pre_invocation_hook, "_get_cue_matched_memory_keys", return_value=["mem_a", "mem_b", "mem_c"]),
        ):
            pre_invocation_hook.main()

        m_status.assert_called_once()
        m_reap.assert_called_once_with(86400)
        m_browseros.assert_called_once()

        out = json.loads(buf.getvalue())
        steps = out.get("injectSteps", [])
        self.assertEqual(len(steps), 1)
        sys_msg = steps[0].get("systemMessage", {}).get("systemMessage", "")
        self.assertTrue(sys_msg.startswith("[Session Grounding Anchor]"))
        self.assertLessEqual(len(sys_msg), 600)
        self.assertIn("AGENTS.md", sys_msg)
        self.assertIn("mem_a, mem_b, mem_c", sys_msg)
        self.assertIn(".agents/hooks.json", sys_msg)
        self.assertIn(".agents/plugins/", sys_msg)
        self.assertTrue(pre_invocation_hook._has_session_start_been_emitted(conv_id))

    def test_session_start_skips_subagent_conversation(self) -> None:
        conv_id = "subagent-session-002"
        payload = {
            "conversationId": conv_id,
            "is_subagent": True,
            "subagentRole": "dev-be",
            "workspacePaths": [self.tmpdir],
        }
        buf = io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["pre_invocation_hook.py", "--session-start"]),
            mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
            mock.patch.object(sys, "stdout", buf),
        ):
            pre_invocation_hook.main()

        out = json.loads(buf.getvalue())
        self.assertEqual(out, {"injectSteps": []})
        self.assertFalse(pre_invocation_hook._has_session_start_been_emitted(conv_id))

    def test_system_sdk_step0_skipped_in_pre_invocation_and_stop_hook(self) -> None:
        tr_path = os.path.join(self.tmpdir, "subagent_transcript.jsonl")
        lines = [
            json.dumps({
                "step_index": 0,
                "source": "SYSTEM_SDK",
                "type": "SYSTEM_MESSAGE",
                "content": "[Session Grounding Anchor] (antigravity_settings)\n- Project Slug: antigravity_settings",
            }),
            json.dumps({
                "step_index": 1,
                "source": "SYSTEM",
                "type": "SYSTEM_MESSAGE",
                "content": "[Active Knowledge Grounding - antigravity_settings]\n- Dynamic Memory Seeds: none",
            }),
            json.dumps({
                "step_index": 2,
                "source": "SYSTEM",
                "type": "SYSTEM_MESSAGE",
                "content": "Execute Shard D1.\n\nallowed_files:\n- config/hooks/pre_invocation_hook.py\n- config/hooks/stop_hook.py\n",
            }),
        ]
        Path(tr_path).write_text("\n".join(lines) + "\n", encoding="utf-8")

        payload = {
            "conversationId": "sub-drift-check",
            "transcriptPath": tr_path,
            "workspacePaths": [REPO_ROOT],
        }
        extracted = pre_invocation_hook._extract_initial_subagent_prompt(payload)
        self.assertIn("allowed_files:", extracted)
        self.assertIn("config/hooks/pre_invocation_hook.py", extracted)

        tracker_file = Path(tempfile.gettempdir()) / ".antigravity_superseded_sub-drift-check.json"
        try:
            tracker_file.write_text(
                json.dumps({os.path.join(REPO_ROOT, "src/unauthorized.py"): True}),
                encoding="utf-8",
            )
            warnings = stop_hook._check_subagent_scope_drift(payload)
            self.assertEqual(len(warnings), 1)
            self.assertIn("unauthorized.py", warnings[0])
        finally:
            tracker_file.unlink(missing_ok=True)

    def test_turn2_skips_statusline_sync_and_turn1_dedups_after_session_start(self) -> None:
        ws = os.path.join(self.tmpdir, "ws_dedup")
        os.makedirs(ws, exist_ok=True)
        Path(os.path.join(ws, "AGENTS.md")).write_text("# Agents\n", encoding="utf-8")

        conv_id = "conv-dedup-001"
        payload_t1 = {
            "conversationId": conv_id,
            "invocationNum": 1,
            "workspacePaths": [ws],
            "lastUserInput": "Fix hook latency",
        }

        # Before .session_start_emitted: preserves full static header & Query Protocol
        full_grounding = pre_invocation_hook._build_turn1_grounding("ws_dedup", ws, payload_t1)
        self.assertIn("[Active Knowledge Grounding - ws_dedup]", full_grounding)
        self.assertIn("Query Protocol:", full_grounding)

        # After .session_start_emitted: omits duplicate static slug header & Query Protocol
        pre_invocation_hook._mark_session_start_emitted(conv_id)
        dedup_grounding = pre_invocation_hook._build_turn1_grounding("ws_dedup", ws, payload_t1)
        self.assertIn("[Active Knowledge Grounding - Turn-1 Dynamic Overlay]", dedup_grounding)
        self.assertNotIn("Query Protocol:", dedup_grounding)

        # Turn 2 skips _ensure_cli_statusline_and_yolo_settings
        payload_t2 = {
            "conversationId": conv_id,
            "invocationNum": 2,
            "workspacePaths": [ws],
        }
        buf = io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["pre_invocation_hook.py"]),
            mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload_t2))),
            mock.patch.object(sys, "stdout", buf),
            mock.patch.object(pre_invocation_hook, "_ensure_cli_statusline_and_yolo_settings") as m_status,
        ):
            pre_invocation_hook.main()
        m_status.assert_not_called()

    def test_herdr_resume_fallback_runs_only_when_session_start_absent(self) -> None:
        conv_id = "conv-resume-herdr"
        payload = {"conversationId": conv_id, "invocationNum": 1}
        with (
            mock.patch.dict(os.environ, {"HERDR_ENV": "1"}, clear=False),
            mock.patch("subprocess.run") as m_run,
        ):
            ran = pre_invocation_hook._maybe_run_herdr_resume_fallback(conv_id, payload)
            self.assertTrue(ran)
            m_run.assert_called_once()

            pre_invocation_hook._mark_session_start_emitted(conv_id)
            m_run.reset_mock()
            ran_after = pre_invocation_hook._maybe_run_herdr_resume_fallback(conv_id, payload)
            self.assertFalse(ran_after)
            m_run.assert_not_called()

    def test_auto_disable_browseros_mcp_zero_write_and_clean_pop(self) -> None:
        fake_home = os.path.join(self.tmpdir, "home_mcp")
        cfg_dir = os.path.join(fake_home, ".gemini", "config")
        os.makedirs(cfg_dir, exist_ok=True)
        mcp_cfg_path = os.path.join(cfg_dir, "mcp_config.json")

        # 1. When browseros-neo is absent, zero write occurs
        clean_cfg = {"mcpServers": {"codegraph": {"command": "codegraph"}}}
        Path(mcp_cfg_path).write_text(json.dumps(clean_cfg), encoding="utf-8")
        with (
            mock.patch.dict(os.environ, {"HOME": fake_home}, clear=False),
            mock.patch("os.replace") as m_replace,
        ):
            pre_invocation_hook._auto_disable_browseros_mcp({"lastUserInput": "hello"})
            m_replace.assert_not_called()

        # 2. When browseros-neo is in mcpServers, pops cleanly without adding disabledMcpServers
        with_browseros = {
            "mcpServers": {
                "codegraph": {"command": "codegraph"},
                "browseros-neo": {"serverUrl": "http://127.0.0.1:9010/mcp"},
            }
        }
        Path(mcp_cfg_path).write_text(json.dumps(with_browseros), encoding="utf-8")
        with mock.patch.dict(os.environ, {"HOME": fake_home}, clear=False):
            pre_invocation_hook._auto_disable_browseros_mcp({"lastUserInput": "hello"})

        updated = json.loads(Path(mcp_cfg_path).read_text(encoding="utf-8"))
        self.assertNotIn("browseros-neo", updated.get("mcpServers", {}))
        self.assertNotIn("disabledMcpServers", updated)

    def test_delivered_inline_syntax_warning_unlinks_and_returns_empty(self) -> None:
        art_dir = os.path.join(self.tmpdir, "artifacts")
        os.makedirs(art_dir, exist_ok=True)
        pending = Path(art_dir) / "syntax_error_pending.json"
        pending.write_text(
            json.dumps({
                "file": "foo.py",
                "error": "SyntaxError: invalid syntax",
                "kind": "syntax",
                "delivered_inline": True,
            }),
            encoding="utf-8",
        )
        msg = pre_invocation_hook._check_and_consume_syntax_warning({"artifactDirectoryPath": art_dir})
        self.assertEqual(msg, "")
        self.assertFalse(pending.exists())

    def test_stop_hook_fully_idle_false_allows_immediately(self) -> None:
        payload = {
            "conversationId": "active-bg-subagents",
            "terminationReason": "model_stop",
            "fullyIdle": False,
        }
        buf = io.StringIO()
        with (
            mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
            mock.patch.object(sys, "stdout", buf),
            mock.patch.object(stop_hook, "_cleanup_action_logs") as m_cleanup,
        ):
            stop_hook.main()

        out = json.loads(buf.getvalue())
        self.assertEqual(out, {"decision": "allow"})
        m_cleanup.assert_not_called()

    def test_agy_sidebar_plugin_mcp_state_discovery(self) -> None:
        fake_home = os.path.join(self.tmpdir, "home_tui")
        cfg_dir = os.path.join(fake_home, ".gemini", "config")
        plugins_dir = os.path.join(cfg_dir, "plugins")
        os.makedirs(os.path.join(plugins_dir, "browseros-neo"), exist_ok=True)
        os.makedirs(os.path.join(plugins_dir, "stitch-mcp"), exist_ok=True)
        os.makedirs(os.path.join(plugins_dir, "open-design"), exist_ok=True)

        mcp_cfg_path = os.path.join(cfg_dir, "mcp_config.json")
        Path(mcp_cfg_path).write_text(
            json.dumps({
                "mcpServers": {
                    "codegraph": {"command": "codegraph"},
                },
                "disabledMcpServers": {
                    "legacy-disabled": {"disabled": True},
                },
            }),
            encoding="utf-8",
        )
        Path(os.path.join(plugins_dir, "browseros-neo", "mcp_config.json")).write_text(
            json.dumps({"mcpServers": {"browseros-neo": {"serverUrl": "http://127.0.0.1:9010/mcp"}}}),
            encoding="utf-8",
        )
        Path(os.path.join(plugins_dir, "browseros-neo", "plugin.json")).write_text(
            json.dumps({"name": "browseros-neo", "disabled": True}),
            encoding="utf-8",
        )
        Path(os.path.join(plugins_dir, "stitch-mcp", "mcp_config.json")).write_text(
            json.dumps({"mcpServers": {"stitch": {"command": "stitch"}}}),
            encoding="utf-8",
        )
        Path(os.path.join(plugins_dir, "stitch-mcp", "plugin.json")).write_text(
            json.dumps({"name": "stitch-mcp", "disabled": True}),
            encoding="utf-8",
        )
        Path(os.path.join(plugins_dir, "open-design", "mcp_config.json")).write_text(
            json.dumps({"mcpServers": {"open-design": {"command": "open-design"}}}),
            encoding="utf-8",
        )
        Path(os.path.join(plugins_dir, "open-design", "plugin.json")).write_text(
            json.dumps({"name": "open-design", "disabled": False}),
            encoding="utf-8",
        )

        # config.json enables browseros-neo, disables open-design, and omits stitch-mcp (falls back to plugin.json disabled=True)
        Path(os.path.join(cfg_dir, "config.json")).write_text(
            json.dumps({
                "plugins": {
                    "browseros-neo": {"enabled": True},
                    "open-design": {"enabled": False},
                }
            }),
            encoding="utf-8",
        )

        sidebar_script = os.path.join(BIN_DIR, "agy-sidebar")
        if not os.path.isfile(sidebar_script):
            fallback = Path("~/.local/bin/agy-sidebar").expanduser()
            sidebar_script = str(fallback) if fallback.is_file() else (shutil.which("agy-sidebar") or sidebar_script)
        with mock.patch.dict(os.environ, {"HOME": fake_home}, clear=False):
            sidebar_mod = runpy.run_path(sidebar_script, run_name="test_sidebar_d1")
            sidebar_mod["MCP_CONFIG_PATH"] = mcp_cfg_path
            get_servers = sidebar_mod["get_configured_mcp_servers"]
            resolve_states = sidebar_mod["resolve_mcp_server_states"]

            active_set = get_servers()
            self.assertEqual(active_set, {"codegraph", "browseros-neo"})

            mcp_active, mcp_disabled = resolve_states()
            self.assertIn("codegraph", mcp_active)
            self.assertIn("browseros-neo", mcp_active)
            self.assertIn("stitch", mcp_disabled)
            self.assertIn("open-design", mcp_disabled)
            self.assertIn("legacy-disabled", mcp_disabled)


if __name__ == "__main__":
    unittest.main()
