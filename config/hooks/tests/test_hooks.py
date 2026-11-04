#!/usr/bin/env python3
"""Hook test suite wrapper / entrypoint for Antigravity hooks."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import io
from unittest.mock import patch

import pre_invocation_hook
import pre_tool_use_hook
import post_tool_use_hook
import stop_hook


class TestContextHealthAlertEnhancement(unittest.TestCase):
    def test_context_health_alert_directives(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            tf.write('{"type": "USER_INPUT", "content": "hello"}\n')
            tf_path = tf.name

        try:
            alert = pre_invocation_hook._check_context_health_alert(
                payload={"conversationId": "test_conv_direct", "transcriptPath": tf_path},
                is_subagent=False,
                invocation_num=20
            )
            self.assertIn("Context Health Alert: DEGRADED", alert)
            self.assertIn("context_health:compact_observations", alert)
            self.assertIn("context_health:commit_context_ledger", alert)
            self.assertIn("/compact", alert)
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)

    def test_context_health_suppressed_after_recent_context_summary(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            # First 30 turns of conversation
            for i in range(30):
                tf.write(json.dumps({"type": "USER_INPUT", "content": f"query {i}"}) + "\n")
                tf.write(json.dumps({"type": "PLANNER_RESPONSE", "content": f"response {i}"}) + "\n")
            # Compaction step
            tf.write(json.dumps({
                "type": "USER_INPUT",
                "content": "<CONTEXT_SUMMARY>\nSummary of previous conversation\n</CONTEXT_SUMMARY>"
            }) + "\n")
            # Only 2 turns after compaction (< 5 turns)
            for i in range(2):
                tf.write(json.dumps({"type": "USER_INPUT", "content": f"post compact {i}"}) + "\n")
                tf.write(json.dumps({"type": "PLANNER_RESPONSE", "content": f"post response {i}"}) + "\n")
            tf_path = tf.name

        try:
            alert = pre_invocation_hook._check_context_health_alert(
                payload={"conversationId": "test_recent_compact", "transcriptPath": tf_path},
                is_subagent=False,
                invocation_num=33
            )
            self.assertEqual(alert, "", "Alert should be suppressed within 5 turns of <CONTEXT_SUMMARY>")
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)

    def test_context_health_triggers_when_turns_since_compact_ge_20(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            # Compaction step
            tf.write(json.dumps({
                "type": "USER_INPUT",
                "content": "<CONTEXT_SUMMARY>\nOld summary\n</CONTEXT_SUMMARY>"
            }) + "\n")
            # Exactly 20 turns after compaction
            for i in range(20):
                tf.write(json.dumps({"type": "USER_INPUT", "content": f"query {i}"}) + "\n")
                tf.write(json.dumps({"type": "PLANNER_RESPONSE", "content": f"response {i}"}) + "\n")
            tf_path = tf.name

        try:
            alert = pre_invocation_hook._check_context_health_alert(
                payload={"conversationId": "test_turns_ge_20", "transcriptPath": tf_path},
                is_subagent=False,
                invocation_num=21
            )
            self.assertIn("Context Health Alert: DEGRADED", alert)
            self.assertIn("/compact", alert)
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)

    def test_context_health_triggers_when_bytes_since_compact_gt_500k(self):
        import uuid
        test_id = f"test_bytes_gt_500k_{uuid.uuid4().hex[:8]}"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            # Compaction step
            tf.write(json.dumps({
                "type": "USER_INPUT",
                "content": "<CONTEXT_SUMMARY>\nOld summary\n</CONTEXT_SUMMARY>"
            }) + "\n")
            # 1 turn after compaction, but with large payload (> 500KB)
            large_blob = "x" * 520_000
            tf.write(json.dumps({"type": "USER_INPUT", "content": large_blob}) + "\n")
            tf_path = tf.name

        try:
            alert = pre_invocation_hook._check_context_health_alert(
                payload={"conversationId": test_id, "transcriptPath": tf_path},
                is_subagent=False,
                invocation_num=2
            )
            self.assertIn("Context Health Alert: DEGRADED", alert)
            self.assertIn("/compact", alert)
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)

    def test_context_health_live_state_active_pct(self):
        import uuid
        test_id = f"test_live_pct_{uuid.uuid4().hex[:8]}"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            for i in range(25):
                tf.write(json.dumps({"type": "USER_INPUT", "content": f"query {i}"}) + "\n")
                tf.write(json.dumps({"type": "PLANNER_RESPONSE", "content": f"resp {i}"}) + "\n")
            tf_path = tf.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as sf:
            state_path = sf.name

        orig_live_path = pre_invocation_hook.LIVE_STATE_PATH
        try:
            pre_invocation_hook.LIVE_STATE_PATH = state_path

            # 1. 12% usage on 1M window -> suppressed despite turn >= 20
            low_state = {
                "conversation_id": test_id,
                "context_window": {
                    "context_window_size": 1_048_576,
                    "current_usage": {
                        "input_tokens": 5_000,
                        "cache_read_input_tokens": 120_000
                    }
                }
            }
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(low_state, f)

            alert = pre_invocation_hook._check_context_health_alert(
                payload={"conversationId": test_id, "transcriptPath": tf_path},
                is_subagent=False,
                invocation_num=25
            )
            self.assertEqual(alert, "", "12% usage should not trigger saturation alert on 1M window")

            # 2. 60% usage on 1M window -> triggers DEGRADED
            high_state = {
                "conversation_id": test_id,
                "context_window": {
                    "context_window_size": 1_048_576,
                    "current_usage": {
                        "input_tokens": 100_000,
                        "cache_read_input_tokens": 530_000
                    }
                }
            }
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(high_state, f)

            alert = pre_invocation_hook._check_context_health_alert(
                payload={"conversationId": test_id, "transcriptPath": tf_path},
                is_subagent=False,
                invocation_num=25
            )
            self.assertIn("Context Health Alert: DEGRADED", alert)
            self.assertIn("60.1%", alert)
        finally:
            pre_invocation_hook.LIVE_STATE_PATH = orig_live_path
            if os.path.isfile(tf_path):
                os.remove(tf_path)
            if os.path.isfile(state_path):
                os.remove(state_path)

    def test_all_role_skill_bundles_exist_on_disk(self):
        for role, (skill_ref, desc) in pre_invocation_hook.ROLE_SKILL_BUNDLES.items():
            refs = skill_ref if isinstance(skill_ref, (list, tuple)) else [skill_ref]
            for r in refs:
                path = os.path.expanduser(r if r.startswith("~") else f"~/.gemini/antigravity/skills/{r}/SKILL.md")
                self.assertTrue(os.path.isfile(path), f"Role '{role}' references non-existent skill: {path}")

    def test_stop_hook_auto_compact_extracts_conv_id_without_name_error(self):
        with tempfile.TemporaryDirectory() as td:
            brain_dir = os.path.join(td, "brain", "12345678-1234-1234-1234-1234567890ab", ".system_generated", "logs")
            os.makedirs(brain_dir, exist_ok=True)
            t_path = os.path.join(brain_dir, "transcript.jsonl")
            with open(t_path, "w") as f:
                f.write('{"type": "USER_INPUT", "content": "hi"}\n')

            payload = {
                "terminationReason": "model_stop",
                "transcriptPath": t_path,
                "invocationNum": 25,
            }
            orig_live_state = getattr(stop_hook, "LIVE_STATE_PATH", None)
            stop_hook.LIVE_STATE_PATH = os.path.join(td, "nonexistent_live_state.json")
            orig_env = os.environ.copy()
            os.environ["TMUX_PANE"] = ""
            os.environ["HERDR_PANE_ID"] = ""
            stamp = "/tmp/agy_autocompact_12345678-1234-1234-1234-1234567890ab.stamp"
            if os.path.isfile(stamp):
                try:
                    os.remove(stamp)
                except Exception:
                    pass
            try:
                stop_hook._maybe_auto_compact(payload)
                self.assertTrue(os.path.isfile(stamp), "Auto-compact stamp must be created")
            except NameError as e:
                self.fail(f"_maybe_auto_compact raised NameError: {e}")
            finally:
                if orig_live_state is not None:
                    stop_hook.LIVE_STATE_PATH = orig_live_state
                os.environ.clear()
                os.environ.update(orig_env)
                if os.path.isfile(stamp):
                    try:
                        os.remove(stamp)
                    except Exception:
                        pass


class TestRemediationHarness(unittest.TestCase):
    def _run_stop(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                stop_hook.main()
                output = mock_out.getvalue().strip()
                return json.loads(output) if output else {}

    def test_strip_json_comments_preserves_urls(self):
        raw = '{"$schema": "https://json.schemastore.org/tsconfig", // inline comment\n "a": 1,\n}'
        cleaned_pre = pre_tool_use_hook._strip_json_comments_and_trailing_commas(raw)
        data_pre = json.loads(cleaned_pre)
        self.assertEqual(data_pre["$schema"], "https://json.schemastore.org/tsconfig")
        self.assertEqual(data_pre["a"], 1)

        cleaned_post = post_tool_use_hook._strip_json_comments_and_trailing_commas(raw)
        data_post = json.loads(cleaned_post)
        self.assertEqual(data_post["$schema"], "https://json.schemastore.org/tsconfig")
        self.assertEqual(data_post["a"], 1)

    def test_stop_hook_retains_simplify_flag_on_allow(self):
        conv_id = "test_simplify_retention_conv_unique"
        simplify_flag = os.path.join(tempfile.gettempdir(), f"antigravity_simplify_alert_{conv_id}.flag")
        Path(simplify_flag).touch()
        self.assertTrue(os.path.isfile(simplify_flag))
        try:
            payload = {
                "conversationId": conv_id,
                "terminationReason": "model_stop",
                "workspacePaths": ["/tmp"],
            }
            res = self._run_stop(payload)
            self.assertEqual(res.get("decision"), "allow")
            self.assertTrue(os.path.isfile(simplify_flag), "simplify_flag_file must not be unlinked on allow")
        finally:
            if os.path.isfile(simplify_flag):
                os.unlink(simplify_flag)

    def test_stop_hook_skips_simplify_gate_when_no_modified_files(self):
        conv_id = "test_simplify_empty_mod_conv_unique"
        with patch.object(stop_hook, "_check_simplify_gate") as mock_simplify:
            payload = {
                "conversationId": conv_id,
                "terminationReason": "model_stop",
                "workspacePaths": ["/tmp"],
            }
            res = self._run_stop(payload)
            self.assertEqual(res.get("decision"), "allow")
            mock_simplify.assert_not_called()


if __name__ == "__main__":
    from test_global_hooks import *  # noqa: F401, F403
    unittest.main()
