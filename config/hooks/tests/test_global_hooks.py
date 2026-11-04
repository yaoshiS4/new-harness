#!/usr/bin/env python3
"""Comprehensive test suite for Antigravity global lifecycle hooks."""
from __future__ import annotations

import hashlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

HOOKS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import pre_tool_use_hook
import pre_invocation_hook
import stop_hook
import post_tool_use_hook


class TestPreToolUseHook(unittest.TestCase):
    def _run_hook(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                pre_tool_use_hook.main()
                output = mock_out.getvalue().strip()
                return json.loads(output) if output else {}

    def test_destructive_command_rm_rf(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "rm -rf /home/heocop/test"}
            }
        })
        self.assertEqual(res.get("decision"), "force_ask")
        self.assertIn("Recursive force removal", res.get("reason", ""))

    def test_destructive_command_git_push(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git push origin main"}
            }
        })
        self.assertEqual(res.get("decision"), "force_ask")
        self.assertIn("Git remote push", res.get("reason", ""))

    def test_destructive_command_git_reset(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git reset --hard HEAD~1"}
            }
        })
        self.assertEqual(res.get("decision"), "force_ask")
        self.assertIn("Destructive git hard reset", res.get("reason", ""))

    def test_dependency_mutation_npm(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "npm install lodash"}
            }
        })
        self.assertEqual(res.get("decision"), "force_ask")
        self.assertIn("Package dependency modification", res.get("reason", ""))

    def test_dependency_mutation_pip(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "pip install requests"}
            }
        })
        self.assertEqual(res.get("decision"), "force_ask")
        self.assertIn("Python package installation", res.get("reason", ""))

    def test_banned_sleep_command(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "echo test && sleep 5"}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Execution of sleep in run_command is strictly forbidden", res.get("reason", ""))

    def test_banned_adb_tap(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "adb shell input tap 200 400"}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Manual ADB coordinate tapping", res.get("reason", ""))

    def test_banned_adb_screencap(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "adb shell screencap /sdcard/screen.png"}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("screencap loops are strictly prohibited", res.get("reason", ""))

    def test_banned_cd_command(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "cd /tmp && ls"}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("The cd command is strictly prohibited", res.get("reason", ""))
        self.assertIn("Use tool-native directory flags", res.get("reason", ""))
        self.assertNotIn("Cwd parameter", res.get("reason", ""))

    def test_allowed_run_command(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git status"}
            }
        })
        self.assertEqual(res.get("decision"), "allow")

    def test_allowed_bare_npm_install(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "npm install"}
            }
        })
        self.assertEqual(res.get("decision"), "allow")

    def test_quoted_arguments_no_false_positive(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": 'git commit -m "fix cd and sleep 5 in bash"'}
            }
        })
        self.assertEqual(res.get("decision"), "allow")

    def test_quoted_git_push_in_grep_no_false_positive(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": 'git log --grep="git push"'}
            }
        })
        self.assertEqual(res.get("decision"), "allow")

    def test_nested_bash_c_destructive_still_intercepted(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": 'bash -c "rm -rf /home/heocop/test"'}
            }
        })
        self.assertEqual(res.get("decision"), "force_ask")

    def test_nested_bash_c_sleep_still_denied(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": 'bash -c "sleep 5"'}
            }
        })
        self.assertEqual(res.get("decision"), "deny")

    def test_view_file_image_blocked(self):
        res = self._run_hook({
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": "/home/heocop/mock/screenshot.png"}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Zero Multimodal Poisoning", res.get("reason", ""))

    def test_view_file_missing_file_blocked(self):
        res = self._run_hook({
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": "/home/heocop/nonexistent_file_xyz_123.ts"}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Pre-Verification Invariant", res.get("reason", ""))

    def test_view_file_existing_file_allowed(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            for i in range(250):
                f.write(f"# line {i}\n")
            test_file = f.name
        try:
            res = self._run_hook({
                "toolCall": {
                    "name": "view_file",
                    "args": {"AbsolutePath": test_file}
                }
            })
            self.assertEqual(res.get("decision"), "allow")
        finally:
            if os.path.isfile(test_file):
                os.remove(test_file)

    def test_bare_npm_test_denied(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "npm test"}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Strict Targeted Test Execution Invariant", res.get("reason", ""))

    def test_bare_npx_vitest_run_denied(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "npx vitest run"}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Strict Targeted Test Execution Invariant", res.get("reason", ""))

    def test_targeted_vitest_run_allowed(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "npx vitest run test/theme/tokens.test.ts"}
            }
        })
        self.assertEqual(res.get("decision"), "allow")

    def test_env_bypass_npm_test_allowed(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "PRE_SHIP=1 npm test"}
            }
        })
        self.assertEqual(res.get("decision"), "allow")

    def test_three_strike_md_file_denied(self):
        test_file = str(Path(__file__).resolve().parent / "dummy_doc.md")
        Path(test_file).write_text("# Dummy Doc\n", encoding="utf-8")
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
                for _ in range(3):
                    tf.write(json.dumps({
                        "tool_calls": [{
                            "name": "view_file",
                            "args": {"AbsolutePath": test_file}
                        }]
                    }) + "\n")
                tf_path = tf.name

            try:
                res = self._run_hook({
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {"AbsolutePath": test_file}
                    }
                })
                self.assertEqual(res.get("decision"), "deny")
                self.assertIn("Three-Strike Rule ACTIVATED", res.get("reason", ""))
            finally:
                if os.path.isfile(tf_path):
                    os.remove(tf_path)
        finally:
            if os.path.isfile(test_file):
                os.remove(test_file)

    def test_mtime_bump_resets_view_file_lockout(self):
        import uuid
        test_conv = f"test_mtime_{uuid.uuid4().hex[:8]}"
        test_file = str(Path(__file__).resolve().parent / "dummy_mtime.ts")
        Path(test_file).write_text("// Dummy mtime test\n" * 10, encoding="utf-8")
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
                for _ in range(3):
                    tf.write(json.dumps({
                        "tool_calls": [{
                            "name": "view_file",
                            "args": {"AbsolutePath": test_file}
                        }]
                    }) + "\n")
                tf_path = tf.name

            try:
                # 1. 3 reads in transcript without edit -> 4th read denied by Three-Strike Rule
                res1 = self._run_hook({
                    "conversationId": test_conv,
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {"AbsolutePath": test_file}
                    }
                })
                self.assertEqual(res1.get("decision"), "deny")
                self.assertIn("Three-Strike Rule ACTIVATED", res1.get("reason", ""))

                # 2. Bump mtime on disk (simulating external edit via run_command / subagent / editor)
                cur_mtime = os.path.getmtime(test_file)
                new_mtime = cur_mtime + 10.0
                os.utime(test_file, (new_mtime, new_mtime))

                # 3. Read again without replace_file_content in transcript -> mtime bump resets lockout!
                res2 = self._run_hook({
                    "conversationId": test_conv,
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {"AbsolutePath": test_file}
                    }
                })
                self.assertEqual(res2.get("decision"), "allow")
            finally:
                if os.path.isfile(tf_path):
                    os.remove(tf_path)
                state_p = Path(f"/tmp/.antigravity_actions_{test_conv}.json")
                if state_p.is_file():
                    state_p.unlink()
        finally:
            if os.path.isfile(test_file):
                os.remove(test_file)

    def test_edit_reset_dampening_at_6_reads(self):
        test_file = str(Path(__file__).resolve().parent / "dummy_code.ts")
        Path(test_file).write_text("// Dummy Code\n" * 350, encoding="utf-8")
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
                # 3 reads, then 1 edit, then 3 reads -> total 6 reads
                for _ in range(3):
                    tf.write(json.dumps({
                        "tool_calls": [{
                            "name": "view_file",
                            "args": {"AbsolutePath": test_file}
                        }]
                    }) + "\n")
                tf.write(json.dumps({
                    "tool_calls": [{
                        "name": "replace_file_content",
                        "args": {"TargetFile": test_file}
                    }]
                }) + "\n")
                for _ in range(3):
                    tf.write(json.dumps({
                        "tool_calls": [{
                            "name": "view_file",
                            "args": {"AbsolutePath": test_file}
                        }]
                    }) + "\n")
                tf_path = tf.name

            try:
                # Whole-file read on 7th read -> should trigger edit-reset loop dampening
                res = self._run_hook({
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {"AbsolutePath": test_file}
                    }
                })
                self.assertEqual(res.get("decision"), "deny")
                self.assertIn("Edit-Reset Loop Dampening ACTIVATED", res.get("reason", ""))

                # Targeted slice read -> should be allowed
                res_slice = self._run_hook({
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {"AbsolutePath": test_file, "StartLine": 1, "EndLine": 5}
                    }
                })
                self.assertEqual(res_slice.get("decision"), "allow")
            finally:
                if os.path.isfile(tf_path):
                    os.remove(tf_path)
        finally:
            if os.path.isfile(test_file):
                os.remove(test_file)

    def test_incremental_cache_and_error_message_lookahead_exclusion(self):
        import hashlib
        import uuid
        test_file = str(Path(__file__).resolve().parent / "dummy_cached.ts")
        Path(test_file).write_text("// Dummy Cached Code\n" * 350, encoding="utf-8")
        conv_id = f"test_cache_conv_{uuid.uuid4().hex[:8]}"
        act_file = Path(tempfile.gettempdir()) / f".antigravity_actions_{conv_id}.json"
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
                # Step 1: 1 whole read
                tf.write(json.dumps({
                    "tool_calls": [{
                        "name": "view_file",
                        "args": {"AbsolutePath": test_file}
                    }]
                }) + "\n")
                tf_path = tf.name

            cache_key = hashlib.sha256(f"{conv_id}:{os.path.abspath(tf_path)}".encode("utf-8")).hexdigest()[:16]
            cache_file = os.path.join(tempfile.gettempdir(), f".antigravity_reads_{cache_key}.json")
            if os.path.isfile(cache_file):
                os.remove(cache_file)

            try:
                # First invocation: parses step 1, holds as pending_step, tentatively total_reads=1
                res = self._run_hook({
                    "conversationId": conv_id,
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {"AbsolutePath": test_file}
                    }
                })
                # Total reads = 1 (whole), second whole read is allowed (< 2 whole reads)
                self.assertEqual(res.get("decision"), "allow")
                self.assertTrue(os.path.isfile(cache_file), "Cache file must exist after first run")
                with open(cache_file, "r", encoding="utf-8") as cf:
                    cdata = json.load(cf)
                self.assertIsNotNone(cdata.get("pending_step"))
                self.assertGreater(cdata.get("offset"), 0)

                # Now simulate that this tool call was rejected by appending ERROR_MESSAGE
                with open(tf_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"type": "ERROR_MESSAGE", "content": "Tool rejected"}) + "\n")

                # Second invocation: should resolve pending_step as rejected and discard it
                res2 = self._run_hook({
                    "conversationId": conv_id,
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {"AbsolutePath": test_file}
                    }
                })
                self.assertEqual(res2.get("decision"), "allow")
                with open(cache_file, "r", encoding="utf-8") as cf:
                    cdata2 = json.load(cf)
                # Since step 1 was rejected by ERROR_MESSAGE, test_file in files should have total_reads == 0
                test_entry = cdata2.get("files", {}).get(pre_tool_use_hook._normalize(test_file, os.getcwd()), {})
                self.assertEqual(test_entry.get("total_reads", 0), 0)

                # Now append 2 valid whole reads
                with open(tf_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "tool_calls": [{
                            "name": "view_file",
                            "args": {"AbsolutePath": test_file}
                        }]
                    }) + "\n")
                    f.write(json.dumps({
                        "tool_calls": [{
                            "name": "view_file",
                            "args": {"AbsolutePath": test_file}
                        }]
                    }) + "\n")

                # Third invocation: 2 whole reads committed/pending -> 3rd whole read denied!
                res3 = self._run_hook({
                    "conversationId": conv_id,
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {"AbsolutePath": test_file}
                    }
                })
                self.assertEqual(res3.get("decision"), "deny")
                self.assertIn("ACTIVATED", res3.get("reason", ""))
            finally:
                if os.path.isfile(tf_path):
                    os.remove(tf_path)
                if os.path.isfile(cache_file):
                    os.remove(cache_file)
                if act_file.is_file():
                    act_file.unlink()
        finally:
            if os.path.isfile(test_file):
                os.remove(test_file)

    def test_unbounded_find_denied(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "find ."}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Legacy `find` is strictly forbidden", res.get("reason", ""))

    def test_bounded_find_denied_legacy_invariant(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "find . -maxdepth 2 -name '*.py'"}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Use `fd` instead", res.get("reason", ""))

    def test_modern_fd_allowed(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "fd -e py --max-results 20 ."}
            }
        })
        self.assertEqual(res.get("decision"), "allow")

    def test_unbounded_tree_and_ls_r_denied(self):
        res_tree = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "tree"}
            }
        })
        self.assertEqual(res_tree.get("decision"), "deny")
        self.assertIn("Unbounded `tree` detected", res_tree.get("reason", ""))

        res_ls = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "ls -laR"}
            }
        })
        self.assertEqual(res_ls.get("decision"), "deny")
        self.assertIn("Recursive `ls -R` detected", res_ls.get("reason", ""))

    def test_monolithic_file_blocked_on_read_one(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            for i in range(1200):
                f.write(f"# line {i}\n")
            big_file = f.name
        try:
            res = self._run_hook({
                "toolCall": {
                    "name": "view_file",
                    "args": {"AbsolutePath": big_file}
                }
            })
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Outline-First Monolithic File Guard", res.get("reason", ""))
        finally:
            if os.path.isfile(big_file):
                os.remove(big_file)

    def test_manage_task_repetitive_status_denied(self):
        conv_id = "test_polling_conv_123"
        state_file = Path(f"/tmp/.antigravity_actions_{conv_id}.json")
        try:
            # First call -> allowed
            res1 = self._run_hook({
                "conversationId": conv_id,
                "toolCall": {
                    "name": "manage_task",
                    "args": {"Action": "status", "TaskId": "task-999"}
                }
            })
            self.assertEqual(res1.get("decision"), "allow")

            # Second call -> denied
            res2 = self._run_hook({
                "conversationId": conv_id,
                "toolCall": {
                    "name": "manage_task",
                    "args": {"Action": "status", "TaskId": "task-999"}
                }
            })
            self.assertEqual(res2.get("decision"), "deny")
            self.assertIn("Anti-Polling Invariant", res2.get("reason", ""))
        finally:
            if state_file.is_file():
                state_file.unlink()

    def test_small_file_slice_fails_with_read_once_not_slice_boundary(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
            for i in range(105):
                f.write(f"const x{i} = {i};\n")
            test_file = f.name
        try:
            res = self._run_hook({
                "toolCall": {
                    "name": "view_file",
                    "args": {"AbsolutePath": test_file, "StartLine": 1, "EndLine": 60}
                }
            })
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Read-Once Policy Invariant", res.get("reason", ""))
            self.assertNotIn("Slice window", res.get("reason", ""))
        finally:
            if os.path.isfile(test_file):
                os.remove(test_file)

    def test_consecutive_identical_actions_circuit_breaker(self):
        conv_id = "test_loop_conv_456"
        state_file = Path(f"/tmp/.antigravity_actions_{conv_id}.json")
        try:
            for _ in range(2):
                res = self._run_hook({
                    "conversationId": conv_id,
                    "toolCall": {
                        "name": "run_command",
                        "args": {"CommandLine": "git status -s"}
                    }
                })
                self.assertEqual(res.get("decision"), "allow")

            # 3rd identical call
            res3 = self._run_hook({
                "conversationId": conv_id,
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": "git status -s"}
                }
            })
            self.assertEqual(res3.get("decision"), "deny")
            self.assertIn("Circuit Breaker ACTIVATED", res3.get("reason", ""))
        finally:
            if state_file.is_file():
                state_file.unlink()

    def test_multiline_dotall_quote_stripping(self):
        cmd = 'python3 -c "\nimport os\nrm -rf /tmp/test\n"'
        stripped = pre_tool_use_hook._strip_safe_quoted_strings(cmd)
        self.assertEqual(stripped, 'python3 -c ""')

        # Hook allows execution because inner rm -rf is stripped safely
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": cmd}
            }
        })
        self.assertEqual(res.get("decision"), "allow")

    def test_unconstrained_command_non_stuttering_prefix(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "git log"}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        reason = res.get("reason", "")
        self.assertTrue(reason.startswith("Token Economy Invariant: "))
        self.assertNotIn("Token Economy Invariant: Token Economy Invariant:", reason)

    def test_recommendations_use_rg_and_fd(self):
        # 1. list_dir on dependency dir recommends fd --max-depth 2
        res_list = self._run_hook({
            "toolCall": {
                "name": "list_dir",
                "args": {"DirectoryPath": "/workspace/node_modules"}
            }
        })
        self.assertEqual(res_list.get("decision"), "deny")
        reason_list = res_list.get("reason", "")
        self.assertIn("fd --max-depth 2", reason_list)
        self.assertNotIn("find <dir> -maxdepth 2", reason_list)

        # 2. view_file excessive slice reads recommends rg -n instead of rgrep -n
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tf_code:
            tf_code.write("# python code line\n" * 50)
            code_path = tf_code.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf_trans:
            for _ in range(6):
                tf_trans.write(json.dumps({
                    "tool_calls": [{
                        "name": "view_file",
                        "args": {"AbsolutePath": code_path, "StartLine": 1, "EndLine": 10}
                    }]
                }) + "\n")
            trans_path = tf_trans.name

        try:
            res_view = self._run_hook({
                "transcriptPath": trans_path,
                "conversationId": "test-conv-slice-rg-rec",
                "toolCall": {
                    "name": "view_file",
                    "args": {"AbsolutePath": code_path, "StartLine": 11, "EndLine": 20}
                }
            })
            self.assertEqual(res_view.get("decision"), "deny")
            reason_view = res_view.get("reason", "")
            self.assertIn("rg -n", reason_view)
            self.assertNotIn("rgrep -n", reason_view)
        finally:
            if os.path.isfile(code_path):
                os.remove(code_path)
            if os.path.isfile(trans_path):
                os.remove(trans_path)

    def test_get_cumulative_reads_retains_ledger_over_64kb(self):
        conv_id = "test-conv-ledger-retention-64kb"
        target_file = "/workspace/tracked.py"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            tf.write(json.dumps({
                "tool_calls": [{
                    "name": "view_file",
                    "args": {"AbsolutePath": target_file}
                }]
            }) + "\n")
            tf.flush()
            tf_path = tf.name

        try:
            # First read populates cache with 1 view_file
            res1 = pre_tool_use_hook._get_or_update_read_ledger(tf_path, conv_id, "/workspace", target_file)
            self.assertEqual(res1[1], 1)  # total_reads == 1

            # Append > 65536 bytes of other log entries and another view_file
            with open(tf_path, "a", encoding="utf-8") as f:
                padding = json.dumps({"type": "MESSAGE", "content": "x" * 1000}) + "\n"
                for _ in range(70):  # 70 * ~1000 > 65536 bytes
                    f.write(padding)
                f.write(json.dumps({
                    "tool_calls": [{
                        "name": "view_file",
                        "args": {"AbsolutePath": target_file}
                    }]
                }) + "\n")
                f.flush()

            # Second read: delta > 64KB, but ledger must retain existing read count
            res2 = pre_tool_use_hook._get_or_update_read_ledger(tf_path, conv_id, "/workspace", target_file)
            self.assertEqual(res2[1], 2)  # total_reads must be 2, not reset to 1
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)
            import hashlib
            ckey = hashlib.sha256(f"{conv_id}:{os.path.abspath(tf_path)}".encode("utf-8")).hexdigest()[:16]
            cfile = os.path.join(tempfile.gettempdir(), f".antigravity_reads_{ckey}.json")
            if os.path.isfile(cfile):
                os.remove(cfile)


class TestPreInvocationHook(unittest.TestCase):
    def _run_hook(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                pre_invocation_hook.main()
                output = mock_out.getvalue().strip()
                return json.loads(output) if output else {}

    def test_turn_one_grounding(self):
        res = self._run_hook({
            "invocationNum": 1,
            "workspacePaths": ["/home/heocop/Projects/lich-viet-v3"]
        })
        inject = res.get("injectSteps", [])
        self.assertEqual(len(inject), 1)
        self.assertIn("Active Knowledge Grounding", inject[0].get("ephemeralMessage", ""))
        self.assertIn("SOL Verification Gates: Active", inject[0].get("ephemeralMessage", ""))

    def test_auto_ensure_verification_gates_and_git_hook(self):
        import tempfile
        import shutil
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Create a mock repo
            (temp_dir / ".git").mkdir()
            (temp_dir / "pyproject.toml").write_text("[project]\nname = 'mock-pkg'\n")

            # Run hook on turn 1 with explicit opt-in
            with patch.dict(os.environ, {"AUTO_VERIFY_GATES": "1", "AGY_INSTALL_GIT_PRECOMMIT": "1"}):
                res = self._run_hook({
                    "invocationNum": 1,
                    "workspacePaths": [str(temp_dir)]
                })

            # Verify gates created
            oracle_sh = temp_dir / "scripts" / "verification" / "verify-oracle.sh"
            test3_sh = temp_dir / "scripts" / "verification" / "test-3-round-loop.sh"
            pre_commit = temp_dir / ".git" / "hooks" / "pre-commit"

            self.assertTrue(oracle_sh.is_file(), "verify-oracle.sh should be auto-installed")
            self.assertTrue(os.access(oracle_sh, os.X_OK), "verify-oracle.sh must be executable")
            self.assertTrue(test3_sh.is_file(), "test-3-round-loop.sh should be auto-installed")
            self.assertTrue(os.access(test3_sh, os.X_OK), "test-3-round-loop.sh must be executable")
            self.assertTrue(pre_commit.is_file(), "git pre-commit hook should be auto-installed")
            self.assertTrue(os.access(pre_commit, os.X_OK), "git pre-commit hook must be executable")
            self.assertIn("verify-oracle.sh", pre_commit.read_text())

            # Verify ephemeral message mentions active gates
            inject = res.get("injectSteps", [])
            self.assertEqual(len(inject), 1)
            self.assertIn("SOL Verification Gates: Active", inject[0].get("ephemeralMessage", ""))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_auto_ensure_verification_gates_git_hook_disabled_by_default(self):
        import tempfile
        import shutil
        temp_dir = Path(tempfile.mkdtemp())
        try:
            (temp_dir / ".git").mkdir()
            (temp_dir / "pyproject.toml").write_text("[project]\nname = 'mock-pkg'\n")

            with patch.dict(os.environ, {"AUTO_VERIFY_GATES": "1"}):
                res = self._run_hook({
                    "invocationNum": 1,
                    "workspacePaths": [str(temp_dir)]
                })

            oracle_sh = temp_dir / "scripts" / "verification" / "verify-oracle.sh"
            pre_commit = temp_dir / ".git" / "hooks" / "pre-commit"
            self.assertTrue(oracle_sh.is_file(), "verify-oracle.sh should be auto-installed when AUTO_VERIFY_GATES=1")
            self.assertFalse(pre_commit.exists(), "pre-commit hook must NOT be installed without AGY_INSTALL_GIT_PRECOMMIT=1")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_auto_ensure_verification_gates_disabled_by_default(self):
        import tempfile
        import shutil
        temp_dir = Path(tempfile.mkdtemp())
        try:
            (temp_dir / ".git").mkdir()
            (temp_dir / "pyproject.toml").write_text("[project]\nname = 'mock-pkg'\n")

            # Run hook on turn 1 without opt-in
            with patch.dict(os.environ, {}, clear=True):
                res = self._run_hook({
                    "invocationNum": 1,
                    "workspacePaths": [str(temp_dir)]
                })

            oracle_sh = temp_dir / "scripts" / "verification" / "verify-oracle.sh"
            self.assertFalse(oracle_sh.exists(), "verify-oracle.sh should NOT be auto-installed by default")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_turn_two_silent(self):
        res = self._run_hook({
            "invocationNum": 2,
            "workspacePaths": ["/home/heocop/Projects/lich-viet-v3"]
        })
        inject = res.get("injectSteps", [])
        self.assertEqual(len(inject), 0)

    def test_turn_25_milestone_checkpoint(self):
        res = self._run_hook({
            "invocationNum": 25,
            "workspacePaths": ["/home/heocop/Projects/lich-viet-v3"]
        })
        inject = res.get("injectSteps", [])
        self.assertEqual(len(inject), 1)
        self.assertIn("SOL Milestone Checkpoint - Turn 25", inject[0].get("ephemeralMessage", ""))

    def test_turn_50_silent_under_exponential_backoff(self):
        res = self._run_hook({
            "invocationNum": 50,
            "workspacePaths": ["/home/heocop/Projects/lich-viet-v3"]
        })
        inject = res.get("injectSteps", [])
        self.assertEqual(len(inject), 0)

    def test_turn_75_milestone_checkpoint(self):
        res = self._run_hook({
            "invocationNum": 75,
            "workspacePaths": ["/home/heocop/Projects/lich-viet-v3"]
        })
        inject = res.get("injectSteps", [])
        self.assertEqual(len(inject), 1)
        self.assertIn("SOL Milestone Checkpoint - Turn 75", inject[0].get("ephemeralMessage", ""))

    def test_context_health_saturation_alert_turn_20(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            tf.write(json.dumps({"type": "USER_INPUT", "content": "hello"}) + "\n")
            tf_path = tf.name

        try:
            # Turn 20 with active transcript -> should trigger Context Health Alert
            res = self._run_hook({
                "invocationNum": 20,
                "transcriptPath": tf_path,
                "workspacePaths": ["/home/heocop/Projects/lich-viet-v3"]
            })
            inject = res.get("injectSteps", [])
            self.assertEqual(len(inject), 1)
            self.assertIn("Context Health Alert: DEGRADED", inject[0].get("ephemeralMessage", ""))
            self.assertIn("/compact", inject[0].get("ephemeralMessage", ""))

            # Subagent conversation -> should be suppressed
            with patch("pre_invocation_hook._is_subagent_conversation", return_value=True):
                res_sub = self._run_hook({
                    "invocationNum": 20,
                    "transcriptPath": tf_path,
                    "workspacePaths": ["/home/heocop/Projects/lich-viet-v3"]
                })
                self.assertEqual(len(res_sub.get("injectSteps", [])), 0)
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)

    def test_unverified_plan_triggers_watchdog_turn_two(self):
        with tempfile.TemporaryDirectory() as td:
            plan = Path(td) / "implementation_plan.md"
            plan.write_text("# Feature Plan\n\n## Proposed Changes\nEdit foo.py\n## Verification Plan\nRun pytest\n", encoding="utf-8")
            res = self._run_hook({
                "invocationNum": 2,
                "workspacePaths": [td]
            })
            inject = res.get("injectSteps", [])
            self.assertEqual(len(inject), 1)
            self.assertIn("Autonomous Oracle Plan Gate Watchdog", inject[0].get("ephemeralMessage", ""))

    def test_verified_plan_silent_turn_two(self):
        with tempfile.TemporaryDirectory() as td:
            plan = Path(td) / "implementation_plan.md"
            plan.write_text("# Feature Plan\n\n## Oracle Hardening, Directives & Verification Matrix\nORACLE REVIEW GATEWAY SIGN-OFF: APPROVED\n", encoding="utf-8")
            res = self._run_hook({
                "invocationNum": 2,
                "workspacePaths": [td]
            })
            inject = res.get("injectSteps", [])
            self.assertEqual(len(inject), 0)

    def test_unverified_plan_debounced_on_subsequent_turn(self):
        with tempfile.TemporaryDirectory() as td:
            plan = Path(td) / "implementation_plan.md"
            plan.write_text("# Feature Plan\n\n## Proposed Changes\nEdit bar.py\n## Verification Plan\nRun test\n", encoding="utf-8")
            # First invocation -> triggers watchdog
            res1 = self._run_hook({
                "invocationNum": 2,
                "workspacePaths": [td]
            })
            inject1 = res1.get("injectSteps", [])
            self.assertEqual(len(inject1), 1)
            self.assertIn("Autonomous Oracle Plan Gate Watchdog", inject1[0].get("ephemeralMessage", ""))

            # Subsequent invocation on same plan mtime -> debounced (silent)
            res2 = self._run_hook({
                "invocationNum": 3,
                "workspacePaths": [td]
            })
            inject2 = res2.get("injectSteps", [])
            self.assertEqual(len(inject2), 0)


class TestStopHook(unittest.TestCase):
    def _run_hook(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                stop_hook.main()
                output = mock_out.getvalue().strip()
                return json.loads(output) if output else {}

    def test_stop_normal_allow(self):
        res = self._run_hook({
            "terminationReason": "model_stop",
            "conversationId": "test-conv-normal",
            "transcriptPath": ""
        })
        self.assertEqual(res.get("decision"), "allow")

    def test_stop_audit_triggers_on_4_unpersisted_files(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            for i in range(4):
                tf.write(json.dumps({
                    "tool_calls": [{
                        "name": "replace_file_content",
                        "args": {"TargetFile": f"/tmp/mod_file_{i}.ts"}
                    }]
                }) + "\n")
            tf_path = tf.name

        try:
            res = self._run_hook({
                "terminationReason": "model_stop",
                "transcriptPath": tf_path
            })
            self.assertEqual(res.get("decision"), "continue")
            self.assertIn("Teardown Gate Alert", res.get("reason", ""))
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)

    def test_stop_audit_triggers_on_status_md_update_without_memory(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            tf.write(json.dumps({
                "tool_calls": [{
                    "name": "replace_file_content",
                    "args": {"TargetFile": "/workspace/docs/STATUS.md"}
                }]
            }) + "\n")
            tf_path = tf.name

        try:
            res = self._run_hook({
                "terminationReason": "model_stop",
                "transcriptPath": tf_path
            })
            self.assertEqual(res.get("decision"), "continue")
            self.assertIn("without storing memory delta", res.get("reason", ""))
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)

    def test_stop_audit_allows_with_quoted_tool_name(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            tf.write(json.dumps({
                "tool_calls": [{
                    "name": "replace_file_content",
                    "args": {"TargetFile": '"/workspace/src/app.ts"'}
                }]
            }) + "\n")
            tf.write(json.dumps({
                "tool_calls": [{
                    "name": "call_mcp_tool",
                    "args": {"ToolName": '"memory_store"'}
                }]
            }) + "\n")
            tf.write(json.dumps({
                "tool_calls": [{
                    "name": "run_command",
                    "args": {"CommandLine": "npm test -- tests/app.test.ts"}
                }]
            }) + "\n")
            tf_path = tf.name

        try:
            res = self._run_hook({
                "terminationReason": "model_stop",
                "transcriptPath": tf_path
            })
            self.assertEqual(res.get("decision"), "allow")
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)

    def test_stop_intercepted_on_unverified_plan(self):
        with tempfile.TemporaryDirectory() as td:
            plan = Path(td) / "implementation_plan.md"
            plan.write_text("# Feature Plan\n\n## Proposed Changes\nBuild feature\n", encoding="utf-8")
            res = self._run_hook({
                "terminationReason": "model_stop",
                "workspacePaths": [td],
                "transcriptPath": ""
            })
            self.assertEqual(res.get("decision"), "continue")
            self.assertIn("Autonomous Oracle Plan Gate Alert", res.get("reason", ""))

    def test_stop_allowed_on_verified_plan(self):
        with tempfile.TemporaryDirectory() as td:
            plan = Path(td) / "implementation_plan.md"
            plan.write_text("# Feature Plan\n\n## Oracle Hardening, Directives & Verification Matrix\nORACLE REVIEW GATEWAY SIGN-OFF: APPROVED\n", encoding="utf-8")
            res = self._run_hook({
                "terminationReason": "model_stop",
                "workspacePaths": [td],
                "transcriptPath": ""
            })
            self.assertEqual(res.get("decision"), "allow")

    def test_stop_allowed_when_oracle_warning_already_issued(self):
        with tempfile.TemporaryDirectory() as td:
            plan = Path(td) / "implementation_plan.md"
            plan.write_text("# Feature Plan\n\n## Proposed Changes\nBuild feature\n", encoding="utf-8")
            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
                tf.write(json.dumps({
                    "content": "[Autonomous Oracle Plan Gate Alert] You created implementation_plan.md..."
                }) + "\n")
                tf_path = tf.name

            try:
                res = self._run_hook({
                    "terminationReason": "model_stop",
                    "workspacePaths": [td],
                    "transcriptPath": tf_path
                })
                self.assertEqual(res.get("decision"), "allow")
            finally:
                if os.path.isfile(tf_path):
                    os.remove(tf_path)

    def test_stop_hook_cleans_reads_cache(self):
        import time
        conv_id = "test_cleanup_conv_999"
        tmp_dir = Path(tempfile.gettempdir())
        reads_cache = tmp_dir / f".antigravity_reads_dummy999.json"
        reads_cache.write_text(json.dumps({"conv_id": conv_id, "offset": 100}), encoding="utf-8")

        stale_cache = tmp_dir / f".antigravity_reads_stale999.json"
        stale_cache.write_text(json.dumps({"conv_id": "other", "offset": 50}), encoding="utf-8")
        stale_mtime = time.time() - 90000
        os.utime(str(stale_cache), (stale_mtime, stale_mtime))

        try:
            stop_hook._cleanup_action_logs(conv_id)
            self.assertFalse(reads_cache.is_file(), "Active session reads cache must be removed by stop_hook")
            self.assertFalse(stale_cache.is_file(), "Stale reads cache > 24h must be removed by stop_hook")
        finally:
            if reads_cache.is_file():
                reads_cache.unlink()
            if stale_cache.is_file():
                stale_cache.unlink()


class TestQuoteUnwrappingAndStringLines(unittest.TestCase):
    def _run_hook(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                pre_tool_use_hook.main()
                output = mock_out.getvalue().strip()
                return json.loads(output) if output else {}

    def test_quoted_untargeted_npm_test_is_denied(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": '"npm test"'}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Strict Targeted Test Execution Invariant", res.get("reason", ""))

    def test_quoted_destructive_rm_rf_requires_ask(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": '"rm -rf /tmp/test"'}
            }
        })
        self.assertEqual(res.get("decision"), "force_ask")

    def test_quoted_git_push_requires_ask(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": '"git push origin main"'}
            }
        })
        self.assertEqual(res.get("decision"), "force_ask")

    def test_quoted_sleep_is_denied(self):
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": '"sleep 3"'}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Execution of sleep in run_command is strictly forbidden", res.get("reason", ""))

    def test_string_line_numbers_slicing_allowed_after_three_reads(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
            for i in range(550):
                f.write(f"console.log({i});\n")
            test_file = f.name

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
                for _ in range(3):
                    tf.write(json.dumps({
                        "tool_calls": [{
                            "name": "view_file",
                            "args": {"AbsolutePath": test_file}
                        }]
                    }) + "\n")
                tf_path = tf.name

            try:
                # Slicing with string line numbers "10" and "20" must be allowed for > 500 line files
                res = self._run_hook({
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {
                            "AbsolutePath": f'"{test_file}"',
                            "StartLine": "10",
                            "EndLine": "20"
                        }
                    }
                })
                self.assertEqual(res.get("decision"), "allow")
            finally:
                if os.path.isfile(tf_path):
                    os.remove(tf_path)
        finally:
            if os.path.isfile(test_file):
                os.remove(test_file)

    def test_read_once_policy_blocks_slicing_on_small_files(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            for i in range(120):
                f.write(f"# line {i}\n")
            small_file = f.name

        try:
            res = self._run_hook({
                "toolCall": {
                    "name": "view_file",
                    "args": {
                        "AbsolutePath": small_file,
                        "StartLine": 10,
                        "EndLine": 30
                    }
                }
            })
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Read-Once Policy Invariant", res.get("reason", ""))
        finally:
            if os.path.isfile(small_file):
                os.remove(small_file)

    def test_slice_loop_breaker_blocks_after_six_slices(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            for i in range(600):
                f.write(f"# line {i}\n")
            large_file = f.name

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
                for idx in range(6):
                    tf.write(json.dumps({
                        "tool_calls": [{
                            "name": "view_file",
                            "args": {
                                "AbsolutePath": large_file,
                                "StartLine": idx * 50 + 1,
                                "EndLine": (idx + 1) * 50
                            }
                        }]
                    }) + "\n")
                tf_path = tf.name

            try:
                # 7th slice should be blocked by Slice Loop Breaker
                res = self._run_hook({
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {
                            "AbsolutePath": large_file,
                            "StartLine": 301,
                            "EndLine": 350
                        }
                    }
                })
                self.assertEqual(res.get("decision"), "deny")
                self.assertIn("Slice Loop Breaker ACTIVATED", res.get("reason", ""))
            finally:
                if os.path.isfile(tf_path):
                    os.remove(tf_path)
        finally:
            if os.path.isfile(large_file):
                os.remove(large_file)

    def test_edit_does_not_reset_read_count(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            for i in range(350):
                f.write(f"# line {i}\n")
            target_file = f.name

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
                # 2 whole reads
                for _ in range(2):
                    tf.write(json.dumps({
                        "tool_calls": [{
                            "name": "view_file",
                            "args": {"AbsolutePath": target_file}
                        }]
                    }) + "\n")
                # followed by an edit
                tf.write(json.dumps({
                    "tool_calls": [{
                        "name": "replace_file_content",
                        "args": {"TargetFile": target_file}
                    }]
                }) + "\n")
                tf_path = tf.name

            try:
                # 3rd whole read must still be blocked (edit does NOT reset read counter)
                res = self._run_hook({
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {"AbsolutePath": target_file}
                    }
                })
                self.assertEqual(res.get("decision"), "deny")
                self.assertIn("ACTIVATED", res.get("reason", ""))
            finally:
                if os.path.isfile(tf_path):
                    os.remove(tf_path)
        finally:
            if os.path.isfile(target_file):
                os.remove(target_file)

    def test_slicing_allowed_for_medium_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            for i in range(350):
                f.write(f"# line {i}\n")
            med_file = f.name

        try:
            # Slicing <= 50 lines for a 350-line file is allowed
            res = self._run_hook({
                "toolCall": {
                    "name": "view_file",
                    "args": {
                        "AbsolutePath": med_file,
                        "StartLine": 10,
                        "EndLine": 50
                    }
                }
            })
            self.assertEqual(res.get("decision"), "allow")
        finally:
            if os.path.isfile(med_file):
                os.remove(med_file)

    def test_slice_window_exceeding_250_lines_denied(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            for i in range(300):
                f.write(f"# line {i}\n")
            target_file = f.name

        try:
            # 261 lines requested (> 250 line boundary)
            res = self._run_hook({
                "toolCall": {
                    "name": "view_file",
                    "args": {
                        "AbsolutePath": target_file,
                        "StartLine": 10,
                        "EndLine": 270
                    }
                }
            })
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("exceeds 250-line maximum", res.get("reason", ""))
        finally:
            if os.path.isfile(target_file):
                os.remove(target_file)

    def test_small_file_slice_fallback_after_two_whole_reads(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            for i in range(120):
                f.write(f"# line {i}\n")
            small_file = f.name

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
                for _ in range(2):
                    tf.write(json.dumps({
                        "tool_calls": [{
                            "name": "view_file",
                            "args": {"AbsolutePath": small_file}
                        }]
                    }) + "\n")
                tf_path = tf.name

            try:
                # After 2 whole reads, targeted slicing <= 50 lines is allowed as fallback
                res = self._run_hook({
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {
                            "AbsolutePath": small_file,
                            "StartLine": 10,
                            "EndLine": 30
                        }
                    }
                })
                self.assertEqual(res.get("decision"), "allow")
            finally:
                if os.path.isfile(tf_path):
                    os.remove(tf_path)
        finally:
            if os.path.isfile(small_file):
                os.remove(small_file)

    def test_command_string_length_guard(self):
        long_cmd = "echo " + "x" * 4005
        res = self._run_hook({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": long_cmd}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("4,000 characters", res.get("reason", ""))



class TestSettingsCleanlinessAndExclusivity(unittest.TestCase):
    def test_hooks_json_exclusive_in_config(self):
        home = Path.home()
        config_hooks = home / ".gemini/config/hooks.json"
        antigravity_hooks = home / ".gemini/antigravity/hooks.json"
        plugins_hooks = home / ".gemini/antigravity-cli/plugins/codex-agents-runtime/hooks.json"
        replica_dir = home / ".gemini/config/plugins/codex-agents-runtime"
        config_plugins_hooks = replica_dir / "hooks.json"

        self.assertTrue(config_hooks.is_file(), "~/.gemini/config/hooks.json must exist")
        self.assertFalse(antigravity_hooks.is_file(), "~/.gemini/antigravity/hooks.json must NOT exist (prevents duplicate execution)")
        self.assertFalse(plugins_hooks.is_file(), "plugins hooks.json must NOT exist (prevents duplicate execution)")
        self.assertFalse(config_plugins_hooks.is_file(), "config plugins hooks.json must NOT exist (prevents duplicate execution)")
        self.assertTrue(replica_dir.is_dir(), "~/.gemini/config/plugins/codex-agents-runtime must exist as a directory")
        self.assertFalse(replica_dir.is_symlink(), "~/.gemini/config/plugins/codex-agents-runtime must be a physical directory, NOT a symlink")

    def test_no_stale_graphrag_references_in_active_rules(self):
        agy_home = Path.home() / ".gemini/antigravity"
        active_dirs = [
            agy_home / "rules",
            agy_home / "templates",
            agy_home / "workflows",
            agy_home / "coordination/gates",
            agy_home / "coordination/context_budget",
        ]
        found = []
        for d in active_dirs:
            if not d.is_dir():
                continue
            for f in d.rglob("*.md"):
                if "_archived" in str(f):
                    continue
                content = f.read_text(encoding="utf-8")
                if "graphrag_" in content or "graphrag:" in content:
                    found.append(str(f))

        self.assertEqual(found, [], f"Found stale graphrag references in active files: {found}")

    def test_frontmatter_validity(self):
        import yaml
        rules_dir = Path.home() / ".gemini/antigravity/rules"
        rule_files = list(rules_dir.glob("*.md"))
        if not rule_files:
            rules_dir = Path.home() / ".gemini/config/_archived_rules"
            rule_files = list(rules_dir.glob("*.md"))
        if not rule_files:
            repo_rules_dir = Path(__file__).resolve().parent.parent.parent / "_archived_rules"
            if not repo_rules_dir.is_dir():
                repo_rules_dir = REPO_ROOT / "config" / "_archived_rules"
            rule_files = list(repo_rules_dir.glob("*.md"))
        self.assertGreaterEqual(len(rule_files), 5, "At least 5 rule files should be present")
        for rf in rule_files:
            content = rf.read_text(encoding="utf-8")
            self.assertTrue(content.startswith("---"), f"{rf.name} must start with YAML frontmatter delimiter '---'")
            parts = content.split("---", 2)
            self.assertGreaterEqual(len(parts), 3, f"{rf.name} must have closing '---' for frontmatter")
            meta = yaml.safe_load(parts[1])
            self.assertIsInstance(meta, dict, f"{rf.name} frontmatter must be a dict")
            self.assertIn("name", meta, f"{rf.name} frontmatter missing 'name'")
            self.assertIn("description", meta, f"{rf.name} frontmatter missing 'description'")


class TestPostToolUseHook(unittest.TestCase):
    def _run_hook(self, payload: dict) -> tuple[dict, str]:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
                    post_tool_use_hook.main()
                    output = mock_out.getvalue().strip()
                    err = mock_err.getvalue().strip()
                    return (json.loads(output) if output else {}, err)

    def test_ts_tsx_clean_syntax_allowed(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsx", delete=False) as f:
            f.write(
                "import React from 'react';\n"
                "// Comment with unbalanced delimiter (\n"
                "/* Block comment with { */\n"
                "export const Component = () => {\n"
                "  const str = '{ balanced inside string }';\n"
                "  const regex = /{[0-9]}/g;\n"
                "  const div = 10 / 2;\n"
                "  const msg = `Value: ${ { val: 42 }.val }`;\n"
                "  return <View style={{ width: 100 / 2 }}>{msg}</View>;\n"
                "};\n"
            )
            p = f.name
        try:
            err = post_tool_use_hook._validate_ts_tsx_syntax(p)
            self.assertIsNone(err, f"Valid TSX should have no syntax error: {err}")
        finally:
            if os.path.isfile(p):
                os.remove(p)

    def test_ts_tsx_git_conflict_marker_detected(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsx", delete=False) as f:
            f.write(
                "export const x = 1;\n"
                "<<<<<<< HEAD\n"
                "export const y = 2;\n"
                "=======\n"
                "export const y = 3;\n"
                ">>>>>>> feature-branch\n"
            )
            p = f.name
        try:
            err = post_tool_use_hook._validate_ts_tsx_syntax(p)
            self.assertIsNotNone(err)
            self.assertIn("Git conflict marker detected", err)
        finally:
            if os.path.isfile(p):
                os.remove(p)

    def test_ts_tsx_delimiter_mismatch_detected(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
            f.write("export const foo = [1, 2, 3);\n")
            p = f.name
        try:
            err = post_tool_use_hook._validate_ts_tsx_syntax(p)
            self.assertIsNotNone(err)
            self.assertIn("Mismatched delimiter", err)
        finally:
            if os.path.isfile(p):
                os.remove(p)

    def test_ts_tsx_unclosed_delimiter_detected(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsx", delete=False) as f:
            f.write("export const Foo = () => { return <View />;\n")
            p = f.name
        try:
            err = post_tool_use_hook._validate_ts_tsx_syntax(p)
            self.assertIsNotNone(err)
            self.assertIn("Unclosed delimiter", err)
        finally:
            if os.path.isfile(p):
                os.remove(p)

    def test_post_tool_use_records_and_clears_warning_on_tsx(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            bad_file = Path(td) / "bad.tsx"
            bad_file.write_text("export const x = { a: 1;\n", encoding="utf-8")
            payload = {
                "workspacePaths": [td],
                "toolCall": {
                    "name": "replace_file_content",
                    "args": {"TargetFile": str(bad_file)}
                }
            }
            _, err = self._run_hook(payload)
            self.assertIn("[SWE-Agent Syntax Smoke Guard]", err)
            ws_hash = hashlib.sha256(str(Path(td).resolve()).encode()).hexdigest()[:12]
            warn_file = Path(tempfile.gettempdir()) / f".antigravity_syntax_error_{ws_hash}.json"
            self.assertTrue(warn_file.is_file(), "Pending syntax error file must be created")

            # Now write valid code -> warning must be cleared
            bad_file.write_text("export const x = { a: 1 };\n", encoding="utf-8")
            _, err2 = self._run_hook(payload)
            self.assertEqual(err2, "")
            self.assertFalse(warn_file.is_file(), "Pending syntax error file must be cleared when syntax is valid")


class TestInvokeSubagentSparsificationGate(unittest.TestCase):
    def _run_hook(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                pre_tool_use_hook.main()
                output = mock_out.getvalue().strip()
                return json.loads(output) if output else {}

    def test_valid_subagent_invocation(self):
        res = self._run_hook({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "Subagents": [{
                        "TypeName": "research",
                        "Role": "research-explorer",
                        "Prompt": "Investigate file routes",
                        "Model": "flash"
                    }]
                }
            }
        })
        self.assertEqual(res.get("decision"), "allow")

    def test_invalid_typename_denied(self):
        res = self._run_hook({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "Subagents": [{
                        "TypeName": "dev-fe",
                        "Role": "dev-fe",
                        "Prompt": "Implement feature"
                    }]
                }
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Native TypeName Contract Violation", res.get("reason", ""))
        self.assertIn("TypeName 'dev-fe' is invalid", res.get("reason", ""))

    def test_invalid_model_tier_denied(self):
        res = self._run_hook({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "Subagents": [{
                        "TypeName": "self",
                        "Role": "debugger",
                        "Prompt": "Check logs",
                        "Model": "gpt-4o"
                    }]
                }
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Native Model Contract Violation", res.get("reason", ""))
        self.assertIn("Model 'gpt-4o' is invalid", res.get("reason", ""))

    def test_prompt_length_exceeding_6000_denied(self):
        long_prompt = "A" * 6001
        res = self._run_hook({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "Subagents": [{
                        "TypeName": "self",
                        "Role": "debugger",
                        "Prompt": long_prompt
                    }]
                }
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Pub/Sub Sparsification Invariant", res.get("reason", ""))
        self.assertIn("exceeds 6,000-character ceiling", res.get("reason", ""))

    def test_builder_missing_allowed_files_denied(self):
        res = self._run_hook({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "Subagents": [{
                        "TypeName": "self",
                        "Role": "dev-fe",
                        "Prompt": "Please update the navbar component."
                    }]
                }
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("BMAD Story Shard Lease Invariant", res.get("reason", ""))
        self.assertIn("invoked without an `allowed_files` lease block", res.get("reason", ""))

    def test_builder_with_allowed_files_allowed(self):
        res = self._run_hook({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "Subagents": [{
                        "TypeName": "self",
                        "Role": "dev-be",
                        "Prompt": "allowed_files:\n  - apps/api/src/server.ts\nImplement endpoint"
                    }]
                }
            }
        })
        self.assertEqual(res.get("decision"), "allow")


class TestStopHookLTLVerification(unittest.TestCase):
    def _run_hook(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                stop_hook.main()
                output = mock_out.getvalue().strip()
                return json.loads(output) if output else {}

    def test_ltl_alert_when_code_modified_without_verify(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            tf.write(json.dumps({"type": "USER_INPUT", "content": "make changes"}) + "\n")
            tf.write(json.dumps({
                "tool_calls": [{
                    "name": "replace_file_content",
                    "args": {"TargetFile": "/workspace/src/feature.ts"}
                }]
            }) + "\n")
            tf_path = tf.name

        try:
            res = self._run_hook({
                "terminationReason": "model_stop",
                "transcriptPath": tf_path,
                "conversationId": "test-ltl-unverified"
            })
            self.assertEqual(res.get("decision"), "continue")
            self.assertIn("Verification Gate Alert", res.get("reason", ""))
            self.assertIn("Causal Past LTL Invariant", res.get("reason", ""))
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)
            flag = Path(tempfile.gettempdir()) / "antigravity_verify_alert_test-ltl-unverified.flag"
            if flag.is_file():
                flag.unlink()

    def test_ltl_allowed_when_command_runs_after_code_mutation(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            tf.write(json.dumps({"type": "USER_INPUT", "content": "make changes"}) + "\n")
            tf.write(json.dumps({
                "tool_calls": [{
                    "name": "replace_file_content",
                    "args": {"TargetFile": "/workspace/src/feature.ts"}
                }]
            }) + "\n")
            tf.write(json.dumps({
                "tool_calls": [{
                    "name": "run_command",
                    "args": {"CommandLine": "pytest tests/test_feature.py"}
                }]
            }) + "\n")
            tf_path = tf.name

        try:
            res = self._run_hook({
                "terminationReason": "model_stop",
                "transcriptPath": tf_path,
                "conversationId": "test-ltl-verified"
            })
            self.assertEqual(res.get("decision"), "allow")
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)

    def test_ltl_alert_idempotency_via_flag_and_content(self):
        conv_id = "test-ltl-idempotency"
        flag = Path(tempfile.gettempdir()) / f"antigravity_verify_alert_{conv_id}.flag"
        flag.touch()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            tf.write(json.dumps({"type": "USER_INPUT", "content": "make changes"}) + "\n")
            tf.write(json.dumps({
                "tool_calls": [{
                    "name": "replace_file_content",
                    "args": {"TargetFile": "/workspace/src/feature.ts"}
                }]
            }) + "\n")
            tf_path = tf.name

        try:
            res = self._run_hook({
                "terminationReason": "model_stop",
                "transcriptPath": tf_path,
                "conversationId": conv_id
            })
            # Second attempt with flag touched must be allowed
            self.assertEqual(res.get("decision"), "allow")
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)
            if flag.is_file():
                flag.unlink()


class TestCompiledQCRunnerScript(unittest.TestCase):
    def test_compiled_qc_valid_python(self):
        import subprocess
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tf:
            tf.write("def add(a: int, b: int) -> int:\n    return a + b\n")
            tf_path = tf.name

        try:
            script = str(Path.home() / ".gemini" / "antigravity" / "scripts" / "run-compiled-qc.py")
            proc = subprocess.run([sys.executable, script, "--files", tf_path], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
            data = json.loads(proc.stdout)
            self.assertEqual(data.get("status"), "PASS")
            self.assertEqual(len(data.get("failures", [])), 0)
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)

    def test_compiled_qc_syntax_error_python(self):
        import subprocess
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tf:
            tf.write("def broken_syntax(:\n")
            tf_path = tf.name

        try:
            script = str(Path.home() / ".gemini" / "antigravity" / "scripts" / "run-compiled-qc.py")
            proc = subprocess.run([sys.executable, script, "--files", tf_path], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            data = json.loads(proc.stdout)
            self.assertEqual(data.get("status"), "FAIL")
            self.assertTrue(len(data.get("failures", [])) >= 1)
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)

    def test_compiled_qc_anti_slop_warnings(self):
        import subprocess
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsx", delete=False) as tf:
            tf.write(
                "export const Component = () => (\n"
                "  <Card>\n"
                "    <Card>\n"
                "      <Badge>1</Badge><Badge>2</Badge><Badge>3</Badge><Badge>4</Badge><Badge>5</Badge><Badge>6</Badge><Badge>7</Badge>\n"
                "      <span className='truncate truncate truncate truncate truncate truncate' />\n"
                "    </Card>\n"
                "  </Card>\n"
                ");\n"
            )
            tf_path = tf.name

        try:
            script = str(Path.home() / ".gemini" / "antigravity" / "scripts" / "run-compiled-qc.py")
            proc = subprocess.run([sys.executable, script, "--files", tf_path], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
            data = json.loads(proc.stdout)
            self.assertEqual(data.get("status"), "PASS")
            warns = data.get("anti_slop_warnings", [])
            self.assertEqual(len(warns), 3)
            self.assertTrue(any("L-01" in w for w in warns))
            self.assertTrue(any("L-16" in w for w in warns))
            self.assertTrue(any("D-09" in w for w in warns))
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)


class TestWave1HookRemediations(unittest.TestCase):
    def _run_pre_tool(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                pre_tool_use_hook.main()
                output = mock_out.getvalue().strip()
                return json.loads(output) if output else {}

    def _run_stop(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                stop_hook.main()
                output = mock_out.getvalue().strip()
                return json.loads(output) if output else {}

    def _run_pre_inv(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                pre_invocation_hook.main()
                output = mock_out.getvalue().strip()
                return json.loads(output) if output else {}

    def _run_post_tool(self, payload: dict) -> tuple[dict, str]:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
                    post_tool_use_hook.main()
                    output = mock_out.getvalue().strip()
                    err = mock_err.getvalue().strip()
                    return (json.loads(output) if output else {}, err)

    def test_stop_hook_termination_reasons(self):
        # Abnormal reasons exit allow early before _cleanup_action_logs
        with patch.object(stop_hook, "_cleanup_action_logs") as mock_cleanup:
            for reason in ("user_cancel", "error", "MAX_INVOCATIONS"):
                res = self._run_stop({"terminationReason": reason})
                self.assertEqual(res.get("decision"), "allow", f"Failed for {reason}")
            mock_cleanup.assert_not_called()

        # Normal completion reasons continue processing and invoke _cleanup_action_logs
        with patch.object(stop_hook, "_cleanup_action_logs") as mock_cleanup:
            res = self._run_stop({"terminationReason": "model_stop"})
            self.assertEqual(res.get("decision"), "allow")
            mock_cleanup.assert_called_once()

        for reason in ("NO_TOOL_CALL", "END_TURN", "", None):
            res = self._run_stop({"terminationReason": reason})
            self.assertEqual(res.get("decision"), "allow", f"Failed for {reason}")

    def test_stop_hook_status_update_recommends_document_sync(self):
        conv_id = "test_doc_sync_alert_conv"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            # Transcript showing modified non-app files and status.md updated, but no memory store
            tf.write(json.dumps({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "update status"}) + "\n")
            tf.write(json.dumps({"type": "PLANNER_RESPONSE", "tool_calls": [{"name": "write_to_file", "args": {"TargetFile": "docs/STATUS.md"}}]}) + "\n")
            tf.write(json.dumps({"type": "PLANNER_RESPONSE", "tool_calls": [{"name": "write_to_file", "args": {"TargetFile": "docs/README.md"}}]}) + "\n")
            tf_path = tf.name

        flag_file = Path(tempfile.gettempdir()) / f"antigravity_stop_alert_{conv_id}.flag"
        try:
            if flag_file.is_file():
                flag_file.unlink()
            res = self._run_stop({
                "conversationId": conv_id,
                "transcriptPath": tf_path,
                "terminationReason": "NO_TOOL_CALL",
            })
            self.assertEqual(res.get("decision"), "continue")
            reason_text = res.get("reason", "")
            self.assertIn("document-sync", reason_text)
            self.assertNotIn("sync-project-knowledge.sh", reason_text)
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)
            if flag_file.is_file():
                flag_file.unlink()

    def test_pre_invocation_project_slug_with_project_path(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "registry.sqlite"
            conn = sqlite3.connect(str(db_path))
            conn.execute(
                "CREATE TABLE projects (slug TEXT PRIMARY KEY, project_path TEXT NOT NULL, vault_path TEXT NOT NULL, data_path TEXT NOT NULL);"
            )
            target_ws = "/home/heocop/Projects/my_special_project"
            conn.execute(
                "INSERT INTO projects (slug, project_path, vault_path, data_path) VALUES (?, ?, ?, ?);",
                ("my_special_slug", target_ws, "/vault", "/data")
            )
            conn.commit()
            conn.close()

            with patch("os.path.expanduser", return_value=str(db_path)):
                slug = pre_invocation_hook._resolve_project_slug(target_ws)
                self.assertEqual(slug, "my_special_slug")

    def test_pre_invocation_bitemporal_edges_filtered(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "graph.sqlite"
            conn = sqlite3.connect(str(db_path))
            conn.execute(
                "CREATE TABLE edges (id INTEGER PRIMARY KEY, src TEXT, rel TEXT, dst TEXT, valid_to TEXT);"
            )
            conn.execute("INSERT INTO edges (id, src, rel, dst, valid_to) VALUES (1, 'ActiveNode', 'NAVIGATES_TO', 'Dst1', NULL);")
            conn.execute("INSERT INTO edges (id, src, rel, dst, valid_to) VALUES (2, 'ActiveNode2', 'PROVIDES', 'Dst2', '');")
            conn.execute("INSERT INTO edges (id, src, rel, dst, valid_to) VALUES (3, 'ExpiredNode', 'IMPLEMENTS', 'Dst3', '2026-01-01');")
            conn.commit()
            conn.close()

            with patch("os.path.expanduser", return_value=str(db_path)):
                _, entities = pre_invocation_hook._get_dynamic_seeds("any_slug")
                self.assertIn("ActiveNode", entities)
                self.assertIn("ActiveNode2", entities)
                self.assertNotIn("ExpiredNode", entities)

    def test_pre_invocation_leased_symbols_workspace_isolation(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "codegraph_index.sqlite"
            conn = sqlite3.connect(str(db_path))
            conn.execute(
                "CREATE TABLE symbols (id INTEGER PRIMARY KEY, workspace TEXT, path TEXT, name TEXT, kind TEXT, line INT, end_line INT, exported INT);"
            )
            conn.execute("INSERT INTO symbols VALUES (1, '/ws/alpha', 'src/index.ts', 'AlphaSymbol', 'function', 1, 10, 1);")
            conn.execute("INSERT INTO symbols VALUES (2, '/ws/beta', 'src/index.ts', 'BetaSymbol', 'function', 1, 10, 1);")
            conn.commit()
            conn.close()

            with patch("os.path.expanduser", return_value=str(db_path)):
                syms_alpha = pre_invocation_hook._get_symbols_for_leased_file("src/index.ts", "/ws/alpha", max_symbols=10)
                self.assertEqual(len(syms_alpha), 1)
                self.assertEqual(syms_alpha[0][0], "AlphaSymbol")

                syms_beta = pre_invocation_hook._get_symbols_for_leased_file("src/index.ts", "/ws/beta", max_symbols=10)
                self.assertEqual(len(syms_beta), 1)
                self.assertEqual(syms_beta[0][0], "BetaSymbol")

    def test_pre_invocation_stale_workspace_plan_ignored(self):
        import time
        with tempfile.TemporaryDirectory() as td:
            plan = Path(td) / "implementation_plan.md"
            plan.write_text("# Plan\nInitial unverified plan without oracle section")
            # Set mtime to 2 hours ago
            past_time = time.time() - 7200
            os.utime(str(plan), (past_time, past_time))

            res = self._run_pre_inv({
                "invocationNum": 2,
                "workspacePaths": [td],
            })
            inject_steps = res.get("injectSteps", [])
            plan_alerts = [s for s in inject_steps if "Autonomous Oracle Plan Gate Watchdog" in s.get("ephemeralMessage", "")]
            self.assertEqual(len(plan_alerts), 0, "Stale workspace plan should not trigger watchdog")

            # Update mtime to now
            now_time = time.time()
            os.utime(str(plan), (now_time, now_time))
            res_fresh = self._run_pre_inv({
                "invocationNum": 2,
                "workspacePaths": [td],
            })
            inject_fresh = res_fresh.get("injectSteps", [])
            plan_fresh_alerts = [s for s in inject_fresh if "Autonomous Oracle Plan Gate Watchdog" in s.get("ephemeralMessage", "")]
            self.assertEqual(len(plan_fresh_alerts), 1, "Fresh workspace plan should trigger watchdog")

    def test_pre_tool_use_jev_loop_requires_3_consecutive(self):
        conv_id = "test_loop_conv_3_consec"
        state_file = Path(f"/tmp/.antigravity_actions_{conv_id}.json")
        try:
            if state_file.is_file():
                state_file.unlink()
            # Action 1: distinct tool
            res1 = self._run_pre_tool({
                "conversationId": conv_id,
                "toolCall": {"name": "run_command", "args": {"CommandLine": "git log -n 1"}}
            })
            self.assertEqual(res1.get("decision"), "allow")

            # Action 2: tool B call 1
            res2 = self._run_pre_tool({
                "conversationId": conv_id,
                "toolCall": {"name": "run_command", "args": {"CommandLine": "git status -s"}}
            })
            self.assertEqual(res2.get("decision"), "allow")

            # Action 3: tool B call 2 (must NOT be blocked even though total len >= 3!)
            res3 = self._run_pre_tool({
                "conversationId": conv_id,
                "toolCall": {"name": "run_command", "args": {"CommandLine": "git status -s"}}
            })
            self.assertEqual(res3.get("decision"), "allow")

            # Action 4: tool B call 3 (3 consecutive identical -> blocked!)
            res4 = self._run_pre_tool({
                "conversationId": conv_id,
                "toolCall": {"name": "run_command", "args": {"CommandLine": "git status -s"}}
            })
            self.assertEqual(res4.get("decision"), "deny")
            self.assertIn("Jev Loop Circuit Breaker ACTIVATED", res4.get("reason", ""))
        finally:
            if state_file.is_file():
                state_file.unlink()

    def test_pre_tool_use_cat_flag_skipping(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
            tf.write("\n".join(f"line {i}" for i in range(250)) + "\n")
            tf_path = tf.name

        try:
            res_flag = self._run_pre_tool({
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": f"cat -n {tf_path}"}
                }
            })
            self.assertEqual(res_flag.get("decision"), "deny")
            self.assertIn("Token Economy Invariant: `cat` on", res_flag.get("reason", ""))

            res_flag_a = self._run_pre_tool({
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": f"cat -A {tf_path}"}
                }
            })
            self.assertEqual(res_flag_a.get("decision"), "deny")
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)

    def test_pre_tool_use_bash_c_python_find_string_allowed(self):
        res = self._run_pre_tool({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": 'bash -c "python3 -c \'x = \\"find\\"\'"'}
            }
        })
        self.assertEqual(res.get("decision"), "allow")

        # Real find is still denied
        res_real = self._run_pre_tool({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": 'bash -c "find . -name test"'}
            }
        })
        self.assertEqual(res_real.get("decision"), "deny")
        self.assertIn("Legacy `find` is strictly forbidden", res_real.get("reason", ""))

    def test_pre_tool_use_payload_role_and_shell_write_lease(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            tf.write('{"type": "SYSTEM_MESSAGE", "content": "Role: \\"dev-be\\"\\nallowed_files:\\n- src/allowed.ts\\n"}\n')
            tf_path = tf.name

        try:
            # 1. Non-builder role passed directly in payload metadata
            res_nb = self._run_pre_tool({
                "role": "oracle-review",
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": "echo 'x' > src/app.ts"}
                }
            })
            self.assertEqual(res_nb.get("decision"), "deny")
            self.assertIn("Role Isolation Shell-Write Guard", res_nb.get("reason", ""))

            # 2. Builder subagent attempting shell write on unleased file
            res_unleased = self._run_pre_tool({
                "transcriptPath": tf_path,
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": "echo 'x' > src/unleased.ts"}
                }
            })
            self.assertEqual(res_unleased.get("decision"), "deny")
            self.assertIn("Story Shard File Lease Violation", res_unleased.get("reason", ""))

            # 3. Builder subagent shell write on leased file
            res_leased = self._run_pre_tool({
                "transcriptPath": tf_path,
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": "echo 'x' > src/allowed.ts"}
                }
            })
            self.assertEqual(res_leased.get("decision"), "allow")
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)

    def test_post_tool_use_target_file_key(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            tf = Path(td) / "broken.py"
            tf.write_text("def broken_syntax(:\n", encoding="utf-8")
            ws_hash = hashlib.sha256(str(Path(td).resolve()).encode()).hexdigest()[:12]
            warn_file = Path(tempfile.gettempdir()) / f".antigravity_syntax_error_{ws_hash}.json"
            try:
                _, err = self._run_post_tool({
                    "workspacePaths": [td],
                    "toolCall": {
                        "name": "replace_file_content",
                        "args": {"target_file": str(tf)}
                    }
                })
                self.assertIn("Broken syntax detected", err)
            finally:
                if warn_file.is_file():
                    warn_file.unlink()

    def test_post_tool_use_jsonc_comments_and_trailing_commas(self):
        import shutil
        # 1. Valid .jsonc with comments and trailing commas
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonc", delete=False) as tf:
            tf.write("{\n  // single line comment\n  /* multi\n  line */\n  \"key\": \"value\",\n}\n")
            p_jsonc = tf.name

        # 2. tsconfig.json with comments and trailing comma
        td = tempfile.mkdtemp()
        p_tsconfig = os.path.join(td, "tsconfig.app.json")
        with open(p_tsconfig, "w") as f:
            f.write("{\n  // TS Config\n  \"compilerOptions\": {\n    \"strict\": true,\n  },\n}\n")

        # 3. Standard .json with comments (should fail)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            tf.write("{\n  // illegal in standard json\n  \"key\": \"value\"\n}\n")
            p_std_json = tf.name

        try:
            err_jsonc = post_tool_use_hook._check_json_syntax(p_jsonc)
            self.assertIsNone(err_jsonc, f".jsonc should allow comments: {err_jsonc}")

            err_tsconfig = post_tool_use_hook._check_json_syntax(p_tsconfig)
            self.assertIsNone(err_tsconfig, f"tsconfig should allow comments: {err_tsconfig}")

            err_std = post_tool_use_hook._check_json_syntax(p_std_json)
            self.assertIsNotNone(err_std, "Standard .json must fail on comments")
            self.assertIn("JSONDecodeError", err_std)
        finally:
            if os.path.isfile(p_jsonc):
                os.remove(p_jsonc)
            if os.path.isfile(p_tsconfig):
                os.remove(p_tsconfig)
            if os.path.isdir(td):
                shutil.rmtree(td)
            if os.path.isfile(p_std_json):
                os.remove(p_std_json)

    def test_pre_tool_use_jev_loop_ignores_cosmetic_args(self):
        conv_id = "test_loop_conv_cosmetic"
        state_file = Path(f"/tmp/.antigravity_actions_{conv_id}.json")
        try:
            if state_file.is_file():
                state_file.unlink()

            res1 = self._run_pre_tool({
                "conversationId": conv_id,
                "toolCall": {
                    "name": "run_command",
                    "args": {
                        "CommandLine": "git status -s",
                        "toolSummary": "Check git status 1",
                        "WaitMsBeforeAsync": 1000,
                    },
                },
            })
            self.assertEqual(res1.get("decision"), "allow")

            res2 = self._run_pre_tool({
                "conversationId": conv_id,
                "toolCall": {
                    "name": "run_command",
                    "args": {
                        "CommandLine": "git status -s",
                        "toolSummary": "Check git status 2",
                        "WaitMsBeforeAsync": 2000,
                    },
                },
            })
            self.assertEqual(res2.get("decision"), "allow")

            res3 = self._run_pre_tool({
                "conversationId": conv_id,
                "toolCall": {
                    "name": "run_command",
                    "args": {
                        "CommandLine": "git status -s",
                        "toolSummary": "Check git status 3",
                        "WaitMsBeforeAsync": 3000,
                    },
                },
            })
            self.assertEqual(res3.get("decision"), "deny")
            self.assertIn("Jev Loop Circuit Breaker ACTIVATED", res3.get("reason", ""))
        finally:
            if state_file.is_file():
                state_file.unlink()

    def test_pre_tool_use_jev_loop_alternating_pair(self):
        conv_id = "test_loop_conv_alternating"
        state_file = Path(f"/tmp/.antigravity_actions_{conv_id}.json")
        try:
            if state_file.is_file():
                state_file.unlink()

            call_a = {
                "conversationId": conv_id,
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": "git status -s", "toolSummary": "Status check"},
                },
            }
            call_b = {
                "conversationId": conv_id,
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": "git diff", "toolSummary": "Diff check"},
                },
            }

            for i, call in enumerate([call_a, call_b, call_a, call_b, call_a], start=1):
                res = self._run_pre_tool(call)
                self.assertEqual(res.get("decision"), "allow", f"Call {i} should be allowed")

            res6 = self._run_pre_tool(call_b)
            self.assertEqual(res6.get("decision"), "deny")
            self.assertIn("Jev Loop Circuit Breaker ACTIVATED", res6.get("reason", ""))
            self.assertIn("deterministic_alternating_breaker", res6.get("reason", ""))
        finally:
            if state_file.is_file():
                state_file.unlink()

    def test_stop_hook_jev_harvest_deduplicates_and_scans_window(self):
        conv_id = "test_loop_harvest_mid_window"
        tmp_dir = Path(tempfile.gettempdir())
        state_file = tmp_dir / f".antigravity_actions_{conv_id}.json"
        td = tempfile.mkdtemp()
        test_db = Path(td) / "registry.sqlite"
        old_env = os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB")
        os.environ["ANTIGRAVITY_TEST_REGISTRY_DB"] = str(test_db)
        try:
            if state_file.is_file():
                state_file.unlink()

            actions = [
                {"tool": "run_command", "args": {"CommandLine": "cargo test", "toolSummary": "Run test 1"}},
                {"tool": "run_command", "args": {"CommandLine": "cargo test", "toolSummary": "Run test 2"}},
                {"tool": "run_command", "args": {"CommandLine": "cargo test", "toolSummary": "Run test 3"}},
                {"tool": "run_command", "args": {"CommandLine": "git status"}},
            ]
            state_file.write_text(json.dumps(actions), encoding="utf-8")

            stop_hook._harvest_ephemeral_failures(conv_id, payload={"workspacePaths": ["/tmp/test_ws"]})

            conn = sqlite3.connect(str(test_db))
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM harness_failures WHERE conv_id = ? AND failure_type = 'jev_loop'", (conv_id,))
            count1 = cur.fetchone()[0]
            self.assertEqual(count1, 1, "Mid-window loop should be harvested once")
            conn.close()

            stop_hook._harvest_ephemeral_failures(conv_id, payload={"workspacePaths": ["/tmp/test_ws"]})

            conn = sqlite3.connect(str(test_db))
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM harness_failures WHERE conv_id = ? AND failure_type = 'jev_loop'", (conv_id,))
            count2 = cur.fetchone()[0]
            self.assertEqual(count2, 1, "Second harvest must deduplicate and not double-record")
            conn.close()
        finally:
            if old_env is not None:
                os.environ["ANTIGRAVITY_TEST_REGISTRY_DB"] = old_env
            else:
                os.environ.pop("ANTIGRAVITY_TEST_REGISTRY_DB", None)
            if state_file.is_file():
                state_file.unlink()
            if os.path.isdir(td):
                import shutil
                shutil.rmtree(td, ignore_errors=True)


class TestWave1PreToolGates(unittest.TestCase):
    def _run_pre_tool(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                pre_tool_use_hook.main()
                output = mock_out.getvalue().strip()
                return json.loads(output) if output else {}

    # === SWE-agent Pre-Write In-Memory AST & Syntax Gate ===

    def test_ug01_pre_write_python_ast_valid_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            target = os.path.join(td, "script.py")
            res = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": target, "CodeContent": "def add(a: int, b: int) -> int:\n    return a + b\n"}
                }
            })
            self.assertEqual(res.get("decision"), "allow")

    def test_ug01_pre_write_python_ast_invalid_denied(self):
        with tempfile.TemporaryDirectory() as td:
            target = os.path.join(td, "bad_script.py")
            res = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": target, "CodeContent": "def broken(:\n    pass\n"}
                }
            })
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Pre-Edit Linter Gate (SWE-agent ACI)", res.get("reason", ""))
            self.assertIn("Syntax error in simulated edit to bad_script.py", res.get("reason", ""))

    def test_ug01_pre_write_json_valid_and_invalid(self):
        with tempfile.TemporaryDirectory() as td:
            target_valid = os.path.join(td, "config.json")
            res_val = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": target_valid, "CodeContent": '{"name": "test", "active": true}'}
                }
            })
            self.assertEqual(res_val.get("decision"), "allow")

            target_bad = os.path.join(td, "broken.json")
            res_bad = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": target_bad, "CodeContent": '{"name": "test",}'}
                }
            })
            self.assertEqual(res_bad.get("decision"), "deny")
            self.assertIn("Pre-Edit Linter Gate (SWE-agent ACI)", res_bad.get("reason", ""))

    def test_ug01_pre_write_jsonc_and_tsconfig_with_comments_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            target_jsonc = os.path.join(td, "settings.jsonc")
            res_jsonc = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "write_to_file",
                    "args": {
                        "TargetFile": target_jsonc,
                        "CodeContent": "{\n  // single comment\n  /* multi\n  comment */\n  \"key\": \"value\",\n}"
                    }
                }
            })
            self.assertEqual(res_jsonc.get("decision"), "allow")

            target_tsconfig = os.path.join(td, "tsconfig.json")
            res_tsconfig = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "write_to_file",
                    "args": {
                        "TargetFile": target_tsconfig,
                        "CodeContent": "{\n  // TS Config\n  \"compilerOptions\": {\n    \"strict\": true,\n  },\n}"
                    }
                }
            })
            self.assertEqual(res_tsconfig.get("decision"), "allow")

    def test_ug01_pre_write_yaml_and_toml_syntax(self):
        with tempfile.TemporaryDirectory() as td:
            # YAML
            target_yaml = os.path.join(td, "deploy.yaml")
            res_y_ok = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": target_yaml, "CodeContent": "server:\n  port: 8080\n  env: prod\n"}
                }
            })
            self.assertEqual(res_y_ok.get("decision"), "allow")

            res_y_bad = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": target_yaml, "CodeContent": "server: : : invalid: [}\n"}
                }
            })
            self.assertEqual(res_y_bad.get("decision"), "deny")
            self.assertIn("Pre-Edit Linter Gate (SWE-agent ACI)", res_y_bad.get("reason", ""))

            # TOML
            target_toml = os.path.join(td, "pyproject.toml")
            res_t_ok = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": target_toml, "CodeContent": '[tool.poetry]\nname = "demo"\nversion = "0.1.0"\n'}
                }
            })
            self.assertEqual(res_t_ok.get("decision"), "allow")

            res_t_bad = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": target_toml, "CodeContent": '[tool.poetry]\nname = = broken\n'}
                }
            })
            self.assertEqual(res_t_bad.get("decision"), "deny")
            self.assertIn("Pre-Edit Linter Gate (SWE-agent ACI)", res_t_bad.get("reason", ""))

    def test_ug01_pre_write_shell_syntax(self):
        with tempfile.TemporaryDirectory() as td:
            target_sh = os.path.join(td, "run.sh")
            res_sh_ok = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": target_sh, "CodeContent": "#!/usr/bin/env bash\nset -euo pipefail\necho 'running'\n"}
                }
            })
            self.assertEqual(res_sh_ok.get("decision"), "allow")

            res_sh_bad = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "write_to_file",
                    "args": {"TargetFile": target_sh, "CodeContent": "#!/usr/bin/env bash\nif true; then\n"}
                }
            })
            self.assertEqual(res_sh_bad.get("decision"), "deny")
            self.assertIn("Pre-Edit Linter Gate (SWE-agent ACI)", res_sh_bad.get("reason", ""))

    def test_ug01_replace_file_content_simulated_syntax(self):
        with tempfile.TemporaryDirectory() as td:
            target_py = os.path.join(td, "service.py")
            with open(target_py, "w") as f:
                f.write("def calculate(x):\n    result = x * 2\n    return result\n")

            # Broken replacement introduces syntax error
            res_bad = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "replace_file_content",
                    "args": {
                        "TargetFile": target_py,
                        "StartLine": 2,
                        "EndLine": 2,
                        "TargetContent": "    result = x * 2\n",
                        "ReplacementContent": "    result = (x *\n"
                    }
                }
            })
            self.assertEqual(res_bad.get("decision"), "deny")
            self.assertIn("Pre-Edit Linter Gate (SWE-agent ACI)", res_bad.get("reason", ""))

            # Valid replacement
            res_ok = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "replace_file_content",
                    "args": {
                        "TargetFile": target_py,
                        "StartLine": 2,
                        "EndLine": 2,
                        "TargetContent": "    result = x * 2\n",
                        "ReplacementContent": "    result = x * 4\n"
                    }
                }
            })
            self.assertEqual(res_ok.get("decision"), "allow")

    def test_ug01_multi_replace_file_content_simulated_syntax(self):
        with tempfile.TemporaryDirectory() as td:
            target_py = os.path.join(td, "module.py")
            with open(target_py, "w") as f:
                f.write("a = 1\nb = 2\nc = 3\n")

            res_bad = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "multi_replace_file_content",
                    "args": {
                        "TargetFile": target_py,
                        "ReplacementChunks": [
                            {"TargetContent": "a = 1\n", "ReplacementContent": "a = 10\n"},
                            {"TargetContent": "b = 2\n", "ReplacementContent": "b = (broken\n"},
                        ]
                    }
                }
            })
            self.assertEqual(res_bad.get("decision"), "deny")
            self.assertIn("Pre-Edit Linter Gate (SWE-agent ACI)", res_bad.get("reason", ""))

    # === Aider-Style TargetContent Verification + difflib Fuzzy Line Hints ===

    def test_ug02_replace_file_content_exact_match_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            target_py = os.path.join(td, "main.py")
            with open(target_py, "w") as f:
                f.write("x = 1\ny = 2\nz = 3\nw = 4\n")

            res = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "replace_file_content",
                    "args": {
                        "TargetFile": target_py,
                        "StartLine": 2,
                        "EndLine": 3,
                        "TargetContent": "y = 2\nz = 3\n",
                        "ReplacementContent": "y = 20\nz = 30\n"
                    }
                }
            })
            self.assertEqual(res.get("decision"), "allow")

    def test_ug02_replace_file_content_wrong_lines_hint(self):
        with tempfile.TemporaryDirectory() as td:
            target_py = os.path.join(td, "main.py")
            content = "\n".join([f"line {i}" for i in range(1, 25)]) + "\n"
            with open(target_py, "w") as f:
                f.write(content)

            # TargetContent is at lines 18-19, but agent queries lines 2-4
            res = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "replace_file_content",
                    "args": {
                        "TargetFile": target_py,
                        "StartLine": 2,
                        "EndLine": 4,
                        "TargetContent": "line 18\nline 19\n",
                        "ReplacementContent": "line 18_mod\nline 19_mod\n"
                    }
                }
            })
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Pre-Edit Fuzzy Match Gate (Aider ACI)", res.get("reason", ""))
            self.assertIn("TargetContent actually exists at lines 18-19", res.get("reason", ""))
            self.assertIn("Update StartLine and EndLine to [18, 19]", res.get("reason", ""))

    def test_ug02_replace_file_content_fuzzy_difflib_hint(self):
        with tempfile.TemporaryDirectory() as td:
            target_py = os.path.join(td, "main.py")
            content = "def calculate_total(price, tax):\n    subtotal = price * 1.0\n    total = subtotal + tax\n    return total\n"
            with open(target_py, "w") as f:
                f.write(content)

            # Agent has a slightly corrupted TargetContent (e.g. subtotal = price * 1.05 instead of 1.0)
            res = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "replace_file_content",
                    "args": {
                        "TargetFile": target_py,
                        "StartLine": 2,
                        "EndLine": 3,
                        "TargetContent": "    subtotal = price * 1.05\n    total = subtotal + tax\n",
                        "ReplacementContent": "    total = price + tax\n"
                    }
                }
            })
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Pre-Edit Fuzzy Match Gate (Aider ACI)", res.get("reason", ""))
            self.assertIn("Closest match is at lines 2-3", res.get("reason", ""))
            self.assertIn("similarity", res.get("reason", ""))
            self.assertIn("subtotal = price * 1.0", res.get("reason", ""))

    # === SWE-agent 50-Hit Search Flood Guard on rg / fd ===

    def test_ug04_search_flood_guard_rg_unbounded_denied(self):
        res = self._run_pre_tool({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "rg 'some_identifier'"}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("SWE-agent 50-Hit Search Flood Guard", res.get("reason", ""))
        self.assertIn("Unbounded `rg` detected without output limits", res.get("reason", ""))

    def test_ug04_search_flood_guard_rg_bounded_allowed(self):
        # 1. With -m 50
        res_m = self._run_pre_tool({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "rg -m 50 'some_identifier'"}
            }
        })
        self.assertEqual(res_m.get("decision"), "allow")

        # 2. With -l
        res_l = self._run_pre_tool({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "rg -l 'some_identifier'"}
            }
        })
        self.assertEqual(res_l.get("decision"), "allow")

        # 3. With -c
        res_c = self._run_pre_tool({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "rg -c 'some_identifier'"}
            }
        })
        self.assertEqual(res_c.get("decision"), "allow")

        # 4. With pipe to head
        res_pipe = self._run_pre_tool({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "rg 'some_identifier' | head -n 30"}
            }
        })
        self.assertEqual(res_pipe.get("decision"), "allow")

        # 5. Targeted at single existing file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tf:
            tf.write("print('hello world')\n")
            target_p = tf.name
        try:
            res_file = self._run_pre_tool({
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": f"rg 'hello' {target_p}"}
                }
            })
            self.assertEqual(res_file.get("decision"), "allow")
        finally:
            if os.path.isfile(target_p):
                os.remove(target_p)

    def test_ug04_search_flood_guard_fd_unbounded_denied(self):
        res = self._run_pre_tool({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "fd 'search_pattern'"}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("SWE-agent 50-Hit Search Flood Guard", res.get("reason", ""))
        self.assertIn("Unbounded `fd` detected without output limits", res.get("reason", ""))

    def test_ug04_search_flood_guard_fd_bounded_allowed(self):
        # 1. With --max-results 50
        res_max = self._run_pre_tool({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "fd --max-results 50 'search_pattern'"}
            }
        })
        self.assertEqual(res_max.get("decision"), "allow")

        # 2. With -d 2
        res_d = self._run_pre_tool({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "fd -d 2 'search_pattern'"}
            }
        })
        self.assertEqual(res_d.get("decision"), "allow")

        # 3. With pipe to head
        res_p = self._run_pre_tool({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "fd 'search_pattern' | head -n 20"}
            }
        })
        self.assertEqual(res_p.get("decision"), "allow")

        # 4. Unbounded fd -e py is denied without output bounds
        res_e_unbounded = self._run_pre_tool({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "fd -e py ."}
            }
        })
        self.assertEqual(res_e_unbounded.get("decision"), "deny")
        self.assertIn("SWE-agent 50-Hit Search Flood Guard", res_e_unbounded.get("reason", ""))

        # 5. Bounded fd -e py with --max-results 20 is allowed
        res_e_bounded = self._run_pre_tool({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "fd -e py --max-results 20 ."}
            }
        })
        self.assertEqual(res_e_bounded.get("decision"), "allow")

        # 6. fd with invalid flag -m is treated as unbounded and denied
        res_m_denied = self._run_pre_tool({
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "fd -m 50 foo"}
            }
        })
        self.assertEqual(res_m_denied.get("decision"), "deny")
        self.assertIn("SWE-agent 50-Hit Search Flood Guard", res_m_denied.get("reason", ""))
        self.assertIn("Note: fd does not support -m (use --max-results instead).", res_m_denied.get("reason", ""))
        self.assertIn("fd --max-results 50 foo", res_m_denied.get("reason", ""))
        self.assertNotIn("-m 50 foo", res_m_denied.get("reason", ""))


class TestOracleAuditRemediations(unittest.TestCase):
    def _run_pre_tool(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                pre_tool_use_hook.main()
                output = mock_out.getvalue().strip()
                return json.loads(output) if output else {}

    # === Stale read tracking & tombstone consumption ===

    def test_ug03_stale_read_mutation_only_records_previously_read_files(self):
        conv_id = "test-conv-oracle-03"
        tmp_dir = Path(tempfile.gettempdir())
        tracker_file = tmp_dir / f".antigravity_superseded_{conv_id}.json"
        if tracker_file.exists():
            tracker_file.unlink()

        with tempfile.TemporaryDirectory() as td:
            transcript = os.path.join(td, "transcript.jsonl")
            with open(transcript, "w") as f:
                f.write('{"type": "USER_INPUT"}\n')

            unread_file = os.path.join(td, "unread.py")
            with open(unread_file, "w") as f:
                f.write("print('unread')\n")

            read_file = os.path.join(td, "read_file.py")
            with open(read_file, "w") as f:
                f.write("print('read')\n")

            t_abs = os.path.abspath(transcript)
            cache_key = hashlib.sha256(f"{conv_id}:{t_abs}".encode("utf-8")).hexdigest()[:16]
            ledger_file = tmp_dir / f".antigravity_reads_{cache_key}.json"

            # Ledger only contains read_file
            ledger_data = {
                "conv_id": conv_id,
                "files": {
                    os.path.realpath(read_file): {"total_reads": 1, "read_count": 1}
                }
            }
            ledger_file.write_text(json.dumps(ledger_data), encoding="utf-8")

            payload = {
                "conversationId": conv_id,
                "transcriptPath": transcript,
            }

            try:
                # 1. Mutate unread file -> must NOT record in tracker_file
                post_tool_use_hook._record_stale_read_mutation(payload, unread_file, unread_file)
                self.assertFalse(tracker_file.exists(), "Unread file must not be tombstoned in superseded cache")

                # 2. Mutate read file -> MUST record in tracker_file
                post_tool_use_hook._record_stale_read_mutation(payload, read_file, read_file)
                self.assertTrue(tracker_file.exists(), "Previously read file must be recorded in superseded cache")
                tracked = json.loads(tracker_file.read_text(encoding="utf-8"))
                self.assertIn(read_file, tracked)
                self.assertFalse(tracked[read_file]["delivered"])
            finally:
                if tracker_file.exists():
                    tracker_file.unlink()
                if ledger_file.exists():
                    ledger_file.unlink()

    def test_ug03_check_and_consume_stale_reads_injects_tombstone_once(self):
        conv_id = "test-conv-oracle-consume"
        tmp_dir = Path(tempfile.gettempdir())
        tracker_file = tmp_dir / f".antigravity_superseded_{conv_id}.json"

        tracker_data = {
            "/path/to/module.py": {
                "mutated_at": time.time(),
                "lines": 55,
                "delivered": False
            }
        }
        tracker_file.write_text(json.dumps(tracker_data), encoding="utf-8")

        payload = {"conversationId": conv_id}
        try:
            # First turn: delivers tombstone
            tombstone_1 = pre_invocation_hook._check_and_consume_stale_reads(payload)
            self.assertIn("[Stale-Read Tombstone]", tombstone_1)
            self.assertIn("module.py (55 lines now)", tombstone_1)

            # Second turn: already delivered, returns empty string
            tombstone_2 = pre_invocation_hook._check_and_consume_stale_reads(payload)
            self.assertEqual(tombstone_2, "")
        finally:
            if tracker_file.exists():
                tracker_file.unlink()

    # === Symbol Localization & Keyword Extraction ===

    def test_ug05_extract_prompt_keywords(self):
        prompt = "Please look at the files and refactor AuthenticationController and TokenValidationService for the user"
        keywords = pre_invocation_hook._extract_prompt_keywords(prompt)
        self.assertIn("AuthenticationController", keywords)
        self.assertIn("TokenValidationService", keywords)
        for stopword in ["please", "look", "files"]:
            self.assertNotIn(stopword, [k.lower() for k in keywords])

        xml_prompt = "<USER_REQUEST>Fix UserRepository query in database</USER_REQUEST>"
        xml_keywords = pre_invocation_hook._extract_prompt_keywords(xml_prompt)
        self.assertIn("UserRepository", xml_keywords)
        self.assertIn("query", xml_keywords)

    def test_ug05_get_codegraph_seed_symbol_localization(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, "codegraph_index.sqlite")
            conn = sqlite3.connect(db_path)
            conn.execute(
                "CREATE TABLE symbols (name TEXT, kind TEXT, path TEXT, line INTEGER, end_line INTEGER, exported INTEGER, workspace TEXT)"
            )
            conn.execute(
                "INSERT INTO symbols VALUES ('OrderProcessor', 'class', '/repo/src/order.py', 42, 60, 1, ?)",
                (td,)
            )
            conn.commit()
            conn.close()

            with patch("os.path.expanduser", return_value=db_path):
                seed = pre_invocation_hook._get_codegraph_seed("Please update OrderProcessor implementation", td)
                self.assertIn("Target Symbols (Agentless RepoMap):", seed)
                self.assertIn("OrderProcessor", seed)
                self.assertIn("order.py:42-60", seed)

    # === Edge Cases: StartLine > EndLine, No Fallback, CRLF Normalization, AllowMultiple ===

    def test_edge_case_start_line_greater_than_end_line(self):
        with tempfile.TemporaryDirectory() as td:
            target_py = os.path.join(td, "test_file.py")
            with open(target_py, "w") as f:
                f.write("a = 1\nb = 2\nc = 3\n")

            # 1. In _verify_target_content_fuzzy
            res = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "replace_file_content",
                    "args": {
                        "TargetFile": target_py,
                        "StartLine": 5,
                        "EndLine": 2,
                        "TargetContent": "b = 2\n",
                        "ReplacementContent": "b = 20\n"
                    }
                }
            })
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Invalid line range: StartLine (5) > EndLine (2).", res.get("reason", ""))

            # 2. In _simulate_file_mutation directly
            sim = pre_tool_use_hook._simulate_file_mutation(
                "replace_file_content",
                {"StartLine": 5, "EndLine": 2, "TargetContent": "b = 2\n", "ReplacementContent": "b = 20\n"},
                target_py
            )
            self.assertIsNone(sim)

    def test_edge_case_simulate_no_fallback_when_lines_specified(self):
        with tempfile.TemporaryDirectory() as td:
            target_py = os.path.join(td, "test_file.py")
            with open(target_py, "w") as f:
                f.write("line 1\nline 2\nline 3\nline 4\ntarget_symbol = 100\n")

            # target_symbol is at line 5, but lines 1-2 specified
            sim = pre_tool_use_hook._simulate_file_mutation(
                "replace_file_content",
                {
                    "StartLine": 1,
                    "EndLine": 2,
                    "TargetContent": "target_symbol = 100\n",
                    "ReplacementContent": "target_symbol = 200\n"
                },
                target_py
            )
            self.assertIsNone(sim, "Should return None when target_content is not in specified line window")

    def test_edge_case_crlf_normalization_in_simulate(self):
        with tempfile.TemporaryDirectory() as td:
            target_py = os.path.join(td, "test_crlf.py")
            # Write with CRLF
            with open(target_py, "wb") as f:
                f.write(b"line1\r\nline2\r\ntarget = 1\r\nline4\r\n")

            # Replace with CRLF in target and replacement
            sim = pre_tool_use_hook._simulate_file_mutation(
                "replace_file_content",
                {
                    "StartLine": 3,
                    "EndLine": 3,
                    "TargetContent": "target = 1\r\n",
                    "ReplacementContent": "target = 99\r\n"
                },
                target_py
            )
            self.assertIsNotNone(sim)
            self.assertIn("target = 99", sim)

    def test_edge_case_allow_multiple_true_hint(self):
        with tempfile.TemporaryDirectory() as td:
            target_py = os.path.join(td, "multi.py")
            with open(target_py, "w") as f:
                f.write("val = 0\nval = 0\nval = 0\n")

            # Target exists at lines 1, 2, 3, but query is lines 10-15 with AllowMultiple=True
            res = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "replace_file_content",
                    "args": {
                        "TargetFile": target_py,
                        "StartLine": 10,
                        "EndLine": 15,
                        "AllowMultiple": True,
                        "TargetContent": "val = 0\n",
                        "ReplacementContent": "val = 1\n"
                    }
                }
            })
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Since AllowMultiple=True, expand line range to span all occurrences", res.get("reason", ""))
            self.assertIn("TargetContent occurs 3 times", res.get("reason", ""))

    def test_edge_case_allow_multiple_false_lists_all_occurrence_ranges(self):
        with tempfile.TemporaryDirectory() as td:
            target_py = os.path.join(td, "multi.py")
            with open(target_py, "w") as f:
                f.write("val = 0\nother = 5\nval = 0\n")

            # Target exists at lines 1 and 3, but query is lines 10-15 with AllowMultiple=False
            res = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "replace_file_content",
                    "args": {
                        "TargetFile": target_py,
                        "StartLine": 10,
                        "EndLine": 15,
                        "AllowMultiple": False,
                        "TargetContent": "val = 0\n",
                        "ReplacementContent": "val = 1\n"
                    }
                }
            })
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("AllowMultiple is False; specify the exact line range", res.get("reason", ""))
            self.assertIn("[1, 1]", res.get("reason", ""))
            self.assertIn("[3, 3]", res.get("reason", ""))

    # === Stop Hook Cleanup ===

    def test_stop_hook_preserves_superseded_tracker(self):
        conv_id = "test-conv-stop-superseded"
        tmp_dir = Path(tempfile.gettempdir())
        tracker_file = tmp_dir / f".antigravity_superseded_{conv_id}.json"
        try:
            tracker_file.write_text("{}", encoding="utf-8")
            self.assertTrue(tracker_file.exists())

            stop_hook._cleanup_action_logs(conv_id)
            self.assertTrue(tracker_file.exists(), "stop_hook._cleanup_action_logs must preserve superseded tracker for next turn")
        finally:
            if tracker_file.exists():
                try:
                    tracker_file.unlink()
                except Exception:
                    pass


class TestClaudeKitAndLossMitigations(unittest.TestCase):
    def _run_pre_tool(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                pre_tool_use_hook.main()
                return json.loads(mock_out.getvalue())

    def _run_stop(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                stop_hook.main()
                return json.loads(mock_out.getvalue())

    def _run_pre_inv(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                pre_invocation_hook.main()
                return json.loads(mock_out.getvalue())

    # --- LOSS-01: 1-Turn In-Flight Fuzzy Patch Auto-Application ---

    def test_loss01_replace_file_content_indentation_drift_auto_heals(self):
        with tempfile.TemporaryDirectory() as td:
            target_py = os.path.join(td, "service.py")
            content = "def calculate_total(a, b):\n    result = a + b\n    return result\n"
            with open(target_py, "w") as f:
                f.write(content)

            # Agent sends target content with 2 spaces instead of 4 spaces indentation
            res = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "replace_file_content",
                    "args": {
                        "TargetFile": target_py,
                        "StartLine": 2,
                        "EndLine": 3,
                        "TargetContent": "  result = a + b\n  return result\n",
                        "ReplacementContent": "    result = (a + b) * 2\n    return result\n"
                    }
                }
            })
            self.assertEqual(res.get("decision"), "allow")
            self.assertIn("overwrite", res)
            self.assertEqual(res["overwrite"]["TargetContent"], "    result = a + b\n    return result\n")
            self.assertEqual(res["overwrite"]["StartLine"], 2)
            self.assertEqual(res["overwrite"]["EndLine"], 3)

    def test_loss01_invalid_syntax_in_healed_edit_denied_by_linter(self):
        with tempfile.TemporaryDirectory() as td:
            target_py = os.path.join(td, "service.py")
            content = "def calculate_total(a, b):\n    result = a + b\n    return result\n"
            with open(target_py, "w") as f:
                f.write(content)

            # Indentation drift heals, but replacement introduces Python syntax error
            res = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "replace_file_content",
                    "args": {
                        "TargetFile": target_py,
                        "StartLine": 2,
                        "EndLine": 3,
                        "TargetContent": "  result = a + b\n  return result\n",
                        "ReplacementContent": "    result = a +\n    return\n"
                    }
                }
            })
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Pre-Edit Linter Gate (SWE-agent ACI)", res.get("reason", ""))

    # --- LOSS-02: Session-State Recovery Snapshot ---

    def test_loss02_save_session_state_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            plan_file = os.path.join(td, "implementation_plan.md")
            with open(plan_file, "w") as f:
                f.write("# Plan\nGoal: test")

            transcript_file = os.path.join(td, "transcript.jsonl")
            with open(transcript_file, "w") as f:
                f.write(json.dumps({
                    "tool_calls": [
                        {"name": "replace_file_content", "args": {"TargetFile": "/path/to/app.py"}},
                        {"name": "run_command", "args": {"CommandLine": "pytest tests/test_app.py"}}
                    ]
                }) + "\n")

            conv_id = f"test-loss02-{int(time.time())}"
            stop_hook._save_session_state_snapshot(td, conv_id, transcript_file)

            snapshot_path = Path(os.path.expanduser(f"~/.cache/antigravity_session_states/{conv_id}.md"))
            try:
                self.assertTrue(snapshot_path.is_file())
                snapshot_text = snapshot_path.read_text(encoding="utf-8")
                self.assertIn("## Active Plan", snapshot_text)
                self.assertIn("implementation_plan.md", snapshot_text)
                self.assertIn("## Modified Files", snapshot_text)
                self.assertIn("/path/to/app.py", snapshot_text)
                self.assertIn("## Recent Verification", snapshot_text)
                self.assertIn("pytest tests/test_app.py", snapshot_text)
            finally:
                if snapshot_path.is_file():
                    snapshot_path.unlink()

    def test_loss02_pre_invocation_post_compaction_recovery_surfaced(self):
        conv_id = f"test-loss02-rec-{int(time.time())}"
        cache_dir = Path(os.path.expanduser("~/.cache/antigravity_session_states"))
        cache_dir.mkdir(parents=True, exist_ok=True)
        snapshot_file = cache_dir / f"{conv_id}.md"
        snapshot_file.write_text("# State\n## Active Plan\n- Path: plan.md\n## Modified Files\n- app.py\n## Recent Verification\n- pytest\n")

        try:
            res = self._run_pre_inv({
                "conversationId": conv_id,
                "source": "compact",
                "invocationNum": 2,
                "workspacePaths": [tempfile.gettempdir()]
            })
            inject_steps = res.get("injectSteps", [])
            self.assertTrue(len(inject_steps) > 0)
            ephemeral = inject_steps[0].get("ephemeralMessage", "")
            self.assertIn("[Post-Compaction Recovery Anchor (ClaudeKit)]", ephemeral)
            self.assertIn("## Active Plan", ephemeral)
        finally:
            if snapshot_file.is_file():
                snapshot_file.unlink()
            flag = Path(tempfile.gettempdir()) / f"antigravity_recovery_surfaced_{conv_id}.flag"
            if flag.is_file():
                flag.unlink()

    # --- CK-01: scout-block Build/Vendor Directory Floodgate ---

    def test_ck01_scout_block_node_modules_view_file(self):
        res = self._run_pre_tool({
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": "/workspace/project/node_modules/lodash/index.js"}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Scout-Block Gate (ClaudeKit)", res.get("reason", ""))
        self.assertIn("Traversing generated/vendor directory (node_modules)", res.get("reason", ""))

    def test_ck01_scout_block_dist_list_dir(self):
        res = self._run_pre_tool({
            "toolCall": {
                "name": "list_dir",
                "args": {"DirectoryPath": "/workspace/project/dist"}
            }
        })
        self.assertEqual(res.get("decision"), "deny")
        self.assertIn("Scout-Block Gate (ClaudeKit)", res.get("reason", ""))
        self.assertIn("Traversing generated/vendor directory (dist)", res.get("reason", ""))

    # --- CK-02: privacy-block Secret & Credential File Gate ---

    def test_ck02_privacy_block_env_and_id_rsa(self):
        # .env blocked
        res_env = self._run_pre_tool({
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": "/workspace/project/.env"}
            }
        })
        self.assertEqual(res_env.get("decision"), "deny")
        self.assertIn("Privacy-Block Gate (ClaudeKit)", res_env.get("reason", ""))
        self.assertIn("Reading sensitive credential file (.env)", res_env.get("reason", ""))

        # id_rsa blocked
        res_key = self._run_pre_tool({
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": "/home/user/.ssh/id_rsa"}
            }
        })
        self.assertEqual(res_key.get("decision"), "deny")
        self.assertIn("Privacy-Block Gate (ClaudeKit)", res_key.get("reason", ""))
        self.assertIn("Reading sensitive credential file (id_rsa)", res_key.get("reason", ""))

    def test_ck02_privacy_block_allows_env_example_and_test(self):
        with tempfile.TemporaryDirectory() as td:
            example_file = os.path.join(td, ".env.example")
            with open(example_file, "w") as f:
                f.write("API_KEY=your_key_here\n")
            test_file = os.path.join(td, ".env.test")
            with open(test_file, "w") as f:
                f.write("API_KEY=test_key\n")

            # .env.example allowed
            res_ex = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "view_file",
                    "args": {"AbsolutePath": example_file}
                }
            })
            self.assertEqual(res_ex.get("decision"), "allow")

            # .env.test allowed
            res_test = self._run_pre_tool({
                "workspacePaths": [td],
                "toolCall": {
                    "name": "view_file",
                    "args": {"AbsolutePath": test_file}
                }
            })
            self.assertEqual(res_test.get("decision"), "allow")

    # --- CK-03: simplify-gate helper ---

    def test_ck03_simplify_gate_below_threshold_or_non_git(self):
        with tempfile.TemporaryDirectory() as td:
            # Non-git directory
            res = stop_hook._check_simplify_gate(td, "test_conv")
            self.assertIsNone(res)

    def test_ck03_simplify_gate_breached_trigger(self):
        with tempfile.TemporaryDirectory() as td:
            import subprocess
            subprocess.run(["git", "init"], cwd=td, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=td, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=td, capture_output=True, check=True)

            init_file = os.path.join(td, "init.txt")
            with open(init_file, "w") as f:
                f.write("initial\n")
            subprocess.run(["git", "add", "."], cwd=td, capture_output=True, check=True)
            subprocess.run(["git", "commit", "-m", "initial commit"], cwd=td, capture_output=True, check=True)

            for i in range(9):
                fname = os.path.join(td, f"file_{i}.txt")
                with open(fname, "w") as f:
                    f.write("line\n" * 50)
            subprocess.run(["git", "add", "."], cwd=td, capture_output=True, check=True)

            res = stop_hook._check_simplify_gate(td, "test_conv")
            self.assertIsNotNone(res)
            self.assertIn("Simplify Gate Advisory (ClaudeKit)", res)
            self.assertIn("Large unsimplified diff detected", res)


class TestDynamicGraphMemoryAndObservationalBuffer(unittest.TestCase):
    def test_pre_invocation_seeded_2hop_subgraph_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "graph.sqlite"
            conn = sqlite3.connect(str(db_path))
            conn.execute("""
                CREATE TABLE edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    src TEXT NOT NULL,
                    rel TEXT NOT NULL,
                    dst TEXT NOT NULL,
                    valid_from TEXT,
                    valid_to TEXT,
                    is_current INTEGER DEFAULT 1,
                    layer TEXT DEFAULT 'semantic',
                    weight REAL DEFAULT 1.0,
                    invalidated_at TEXT,
                    superseded_by INTEGER,
                    causal_conv_id TEXT DEFAULT '',
                    payload TEXT DEFAULT '{}'
                );
            """)
            conn.execute("INSERT INTO edges (src, rel, dst, valid_from, is_current, layer) VALUES ('OrderService', 'IMPLEMENTS', 'OrderAPI', '2026-01-01', 1, 'semantic');")
            conn.execute("INSERT INTO edges (src, rel, dst, valid_from, is_current, layer) VALUES ('OrderAPI', 'BROKEN_BY', 'AuthBug', '2026-01-01', 1, 'causal');")
            conn.execute("INSERT INTO edges (src, rel, dst, valid_from, is_current, layer) VALUES ('AuthBug', 'MODIFIED_IN', 'auth.py', '2026-01-01', 1, 'episodic');")
            conn.execute("INSERT INTO edges (src, rel, dst, valid_from, is_current, layer) VALUES ('UnrelatedNode', 'PROVIDES', 'UnrelatedAPI', '2026-01-01', 1, 'semantic');")
            conn.commit()
            conn.close()

            # 1. Test intent classification
            dbg_intent = pre_invocation_hook._classify_graph_intent("fix login bug and crash issue")
            self.assertEqual(dbg_intent["causal"], 1.8)
            self.assertEqual(dbg_intent["episodic"], 1.4)

            time_intent = pre_invocation_hook._classify_graph_intent("when was this previous superseded history")
            self.assertEqual(time_intent["temporal"], 1.8)

            arch_intent = pre_invocation_hook._classify_graph_intent("system overview architecture")
            self.assertEqual(arch_intent["semantic"], 1.5)

            # 2. Test 2-hop traversal with debug query prioritizing AuthBug
            subgraph = pre_invocation_hook._traverse_seeded_subgraph(
                str(db_path),
                prompt_text="fix broken AuthBug in auth module",
                limit=3,
            )
            self.assertTrue(len(subgraph) >= 2)
            rel_list = [r[1] for r in subgraph]
            self.assertTrue("BROKEN_BY" in rel_list or "MODIFIED_IN" in rel_list)

            # 3. Test _get_dynamic_seeds with prompt returns linearized tuples
            with patch("os.path.expanduser", return_value=str(db_path)):
                _, entities = pre_invocation_hook._get_dynamic_seeds("any_slug", prompt_text="fix AuthBug crash")
                self.assertTrue(any("AuthBug" in e for e in entities))
                self.assertTrue(any("-> (" in e for e in entities))

            # 4. Test _get_subagent_graph_triples with allowed_files
            with patch("os.path.expanduser", return_value=str(db_path)):
                triples = pre_invocation_hook._get_subagent_graph_triples(
                    "any_slug",
                    prompt_text="fix AuthBug",
                    allowed_files=["auth.py"],
                )
                self.assertTrue(len(triples) > 0)
                self.assertTrue(any("auth.py" in t or "AuthBug" in t for t in triples))

    def test_stop_hook_folds_episodic_lineage_before_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "graph.sqlite"
            conv_id = "test-conv-fold-1234"
            tmp_dir = Path(tempfile.gettempdir())
            mutations_f = tmp_dir / f".antigravity_mutations_{conv_id}.json"
            actions_f = tmp_dir / f".antigravity_actions_{conv_id}.json"

            mutations_f.write_text(json.dumps(["/src/auth.py", "/src/server.py"]), encoding="utf-8")
            actions_f.write_text(
                json.dumps([
                    {"tool": "run_command", "args": {"CommandLine": "pytest tests/test_auth.py -v"}},
                    {"tool": "read_file", "args": {"Path": "/src/auth.py"}},
                ]),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"ANTIGRAVITY_TEST_GRAPH_DB": str(db_path)}):
                inserted = stop_hook._fold_episodic_lineage_to_graph(
                    conv_id,
                    payload={"workspacePaths": ["/src"]},
                    transcript_path=None,
                )
                self.assertTrue(inserted >= 2)

                # Verify edges written into graph DB
                conn = sqlite3.connect(str(db_path))
                rows = conn.execute("SELECT src, rel, dst, layer, causal_conv_id, recorded_at FROM edges WHERE is_current = 1;").fetchall()
                conn.close()

                srcs = [r[0] for r in rows]
                rels = [r[1] for r in rows]
                dsts = [r[2] for r in rows]
                layers = [r[3] for r in rows]
                convs = [r[4] for r in rows]
                recorded_ats = [r[5] for r in rows]

                session_node = f"session:{conv_id[:8]}"
                self.assertIn(session_node, srcs)
                self.assertIn("MODIFIED_IN", rels)
                self.assertIn("file:auth.py", dsts)
                self.assertIn("VERIFIED_BY", rels)
                self.assertIn("cmd:pytest", dsts)
                self.assertTrue(all(l == "episodic" for l in layers))
                self.assertTrue(all(c == conv_id for c in convs))
                self.assertTrue(all(bool(rec) for rec in recorded_ats))

                # Now verify cleanup unlinks the files
                stop_hook._cleanup_action_logs(conv_id)
                self.assertFalse(mutations_f.exists())
                self.assertFalse(actions_f.exists())

    def test_observational_memory_buffer_observer_reflector(self):
        with tempfile.TemporaryDirectory() as td:
            conv_id = "test-obs-conv-7890"
            transcript_p = Path(td) / "transcript.jsonl"
            lines = [
                json.dumps({"type": "PLANNER_RESPONSE", "tool_calls": [{"name": "read_file", "args": {"Path": "/src/user.py"}}]}),
                json.dumps({"type": "PLANNER_RESPONSE", "tool_calls": [{"name": "read_file", "args": {"Path": "/src/user.py"}}]}),
                json.dumps({"type": "PLANNER_RESPONSE", "tool_calls": [{"name": "read_file", "args": {"Path": "/src/user.py"}}]}),
                json.dumps({"type": "PLANNER_RESPONSE", "tool_calls": [{"name": "edit_file", "args": {"Path": "/src/user.py"}}]}),
                json.dumps({"type": "PLANNER_RESPONSE", "tool_calls": [{"name": "run_command", "args": {"CommandLine": "pytest tests/test_user.py"}}]}),
            ]
            transcript_p.write_text("\n".join(lines) + "\n", encoding="utf-8")

            obs_output = stop_hook._update_observational_memory_buffer(conv_id, str(transcript_p))
            self.assertIsNotNone(obs_output)
            obs_file = Path(os.path.expanduser(f"~/.cache/antigravity_observations/{conv_id}.md"))
            self.assertTrue(obs_file.is_file())

            try:
                content = obs_file.read_text(encoding="utf-8")
                self.assertIn("🔴 Mutations", content)
                self.assertIn("user.py", content)
                self.assertIn("🟡 Verifications", content)
                self.assertIn("pytest tests/test_user.py", content)
                self.assertIn("🟢 Key Reads", content)
                self.assertIn("`user.py` (3 reads)", content)
                self.assertLessEqual(len(content), 2500)

                # Test pre_invocation_hook surfaces observation prefix on high context (turn 20)
                alert = pre_invocation_hook._check_context_health_alert(
                    {"conversationId": conv_id, "transcriptPath": str(transcript_p)},
                    is_subagent=False,
                    invocation_num=20,
                )
                self.assertIn("[Context Health Alert: DEGRADED", alert)
                self.assertIn("[Distilled Observation Prefix]:", alert)
                self.assertIn("user.py", alert)
            finally:
                if obs_file.is_file():
                    obs_file.unlink()

    def test_stop_hook_cli_tool_names_and_path_resolution(self):
        """Test Defect 3: stop_hook recognizes write_file and edit_file with Path argument."""
        with tempfile.TemporaryDirectory() as td:
            conv_id = "test-cli-tools-conv-123"
            transcript_p = Path(td) / "transcript.jsonl"
            lines = [
                json.dumps({
                    "type": "PLANNER_RESPONSE",
                    "tool_calls": [
                        {"name": "write_file", "args": {"Path": "/workspace/src/new_service.py", "Content": "pass"}},
                        {"name": "edit_file", "args": {"Path": "/workspace/src/existing_model.py", "Target": "a", "Replacement": "b"}},
                    ],
                }),
            ]
            transcript_p.write_text("\n".join(lines) + "\n", encoding="utf-8")

            # Call _save_session_state_snapshot to verify snapshot captures CLI tool mutations
            stop_hook._save_session_state_snapshot(td, conv_id, str(transcript_p))

            cache_dir = Path(os.path.expanduser("~/.cache/antigravity_session_states"))
            snapshot_file = cache_dir / f"{conv_id}.md"
            self.assertTrue(snapshot_file.is_file())
            content = snapshot_file.read_text(encoding="utf-8")
            self.assertIn("new_service.py", content)
            self.assertIn("existing_model.py", content)
            snapshot_file.unlink()


class TestTokenLeakAndJevEfficiencyUpgrades(unittest.TestCase):
    """Verifies the 5 token-leak and Jev-efficiency fixes."""

    def _run_pre_tool(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                pre_tool_use_hook.main()
                output = mock_out.getvalue().strip()
                return json.loads(output) if output else {}

    def test_jev_commandline_whitespace_normalization(self):
        """Fix 1: CommandLine whitespace is normalized in _canonical_jev_args for both hooks."""
        raw_cmd = "git   status   -s\n  --branch  "
        expected_normalized_cmd = "git status -s --branch"

        args = {
            "CommandLine": raw_cmd,
            "WaitMsBeforeAsync": 5000,
            "toolSummary": "Git status",
        }
        res_pre = pre_tool_use_hook._canonical_jev_args(args)
        parsed_pre = json.loads(res_pre)
        self.assertEqual(parsed_pre.get("CommandLine"), expected_normalized_cmd)
        self.assertNotIn("WaitMsBeforeAsync", parsed_pre)

        res_stop = stop_hook._canonical_jev_args(args)
        parsed_stop = json.loads(res_stop)
        self.assertEqual(parsed_stop.get("CommandLine"), expected_normalized_cmd)

        # Loop detector triggers despite varying whitespace
        conv_id = f"test_jev_norm_{int(time.time() * 1000)}"
        state_file = Path(tempfile.gettempdir()) / f".antigravity_actions_{conv_id}.json"
        try:
            p1 = {"conversationId": conv_id, "toolCall": {"name": "run_command", "args": {"CommandLine": "git   status  -s"}}}
            p2 = {"conversationId": conv_id, "toolCall": {"name": "run_command", "args": {"CommandLine": "git status   -s"}}}
            p3 = {"conversationId": conv_id, "toolCall": {"name": "run_command", "args": {"CommandLine": "git  status -s"}}}

            r1 = self._run_pre_tool(p1)
            self.assertEqual(r1.get("decision"), "allow")
            r2 = self._run_pre_tool(p2)
            self.assertEqual(r2.get("decision"), "allow")
            r3 = self._run_pre_tool(p3)
            self.assertEqual(r3.get("decision"), "deny")
            self.assertIn("Jev Loop Circuit Breaker", r3.get("reason", ""))
        finally:
            if state_file.is_file():
                state_file.unlink()

    def test_interleaved_task_status_polling_blocked(self):
        """Fix 2a: manage_task(Action='status') blocked when interleaved with read_file."""
        conv_id = f"test_interleaved_task_{int(time.time() * 1000)}"
        state_file = Path(tempfile.gettempdir()) / f".antigravity_actions_{conv_id}.json"
        try:
            # 1. status call -> allowed
            res1 = self._run_pre_tool({
                "conversationId": conv_id,
                "toolCall": {"name": "manage_task", "args": {"Action": "status", "TaskId": "task-alpha"}},
            })
            self.assertEqual(res1.get("decision"), "allow")

            # 2. Interleaved read_file tool call
            res2 = self._run_pre_tool({
                "conversationId": conv_id,
                "toolCall": {"name": "read_file", "args": {"Path": __file__, "StartLine": 1, "EndLine": 50}},
            })
            self.assertEqual(res2.get("decision"), "allow")

            # 3. Interleaved status call on same task -> denied
            res3 = self._run_pre_tool({
                "conversationId": conv_id,
                "toolCall": {"name": "manage_task", "args": {"Action": "status", "TaskId": "task-alpha"}},
            })
            self.assertEqual(res3.get("decision"), "deny")
            self.assertIn("Token Economy & Anti-Polling Invariant", res3.get("reason", ""))
            self.assertIn("task-alpha", res3.get("reason", ""))

            # 4. Different task -> allowed
            res4 = self._run_pre_tool({
                "conversationId": conv_id,
                "toolCall": {"name": "manage_task", "args": {"Action": "status", "TaskId": "task-beta"}},
            })
            self.assertEqual(res4.get("decision"), "allow")
        finally:
            if state_file.is_file():
                state_file.unlink()

    def test_manage_subagents_list_polling_blocked(self):
        """Fix 2b: manage_subagents(Action='list') blocked consecutive and after >= 2 prior calls."""
        conv_id = f"test_manage_subagents_{int(time.time() * 1000)}"
        state_file = Path(tempfile.gettempdir()) / f".antigravity_actions_{conv_id}.json"
        try:
            # Consecutive denial test
            res1 = self._run_pre_tool({
                "conversationId": conv_id,
                "toolCall": {"name": "manage_subagents", "args": {"Action": "list"}},
            })
            self.assertEqual(res1.get("decision"), "allow")

            res2 = self._run_pre_tool({
                "conversationId": conv_id,
                "toolCall": {"name": "manage_subagents", "args": {"Action": "list"}},
            })
            self.assertEqual(res2.get("decision"), "deny")
            self.assertIn("Repetitive `manage_subagents(Action='list')` polling detected", res2.get("reason", ""))
        finally:
            if state_file.is_file():
                state_file.unlink()

        # Interleaved count >= 2 test
        conv_id2 = f"test_manage_subagents_cnt_{int(time.time() * 1000)}"
        state_file2 = Path(tempfile.gettempdir()) / f".antigravity_actions_{conv_id2}.json"
        try:
            # Call 1: list
            res1 = self._run_pre_tool({
                "conversationId": conv_id2,
                "toolCall": {"name": "manage_subagents", "args": {"Action": "list"}},
            })
            self.assertEqual(res1.get("decision"), "allow")

            # Call 2: other tool
            res2 = self._run_pre_tool({
                "conversationId": conv_id2,
                "toolCall": {"name": "run_command", "args": {"CommandLine": "git -C /tmp status -s"}},
            })
            self.assertEqual(res2.get("decision"), "allow")

            # Call 3: list (prior count = 1, not consecutive -> allowed)
            res3 = self._run_pre_tool({
                "conversationId": conv_id2,
                "toolCall": {"name": "manage_subagents", "args": {"Action": "list"}},
            })
            self.assertEqual(res3.get("decision"), "allow")

            # Call 4: other tool
            res4 = self._run_pre_tool({
                "conversationId": conv_id2,
                "toolCall": {"name": "run_command", "args": {"CommandLine": "git -C /tmp branch"}},
            })
            self.assertEqual(res4.get("decision"), "allow")

            # Call 5: list (prior count = 2 >= 2 -> denied)
            res5 = self._run_pre_tool({
                "conversationId": conv_id2,
                "toolCall": {"name": "manage_subagents", "args": {"Action": "list"}},
            })
            self.assertEqual(res5.get("decision"), "deny")
            self.assertIn("Repetitive `manage_subagents(Action='list')` polling detected", res5.get("reason", ""))
        finally:
            if state_file2.is_file():
                state_file2.unlink()

    def test_top_level_invoke_subagent_schema_normalization(self):
        """Fix 3a: Top-level invoke_subagent keys are normalized into subagents list and validated."""
        # Valid top-level
        res_ok = self._run_pre_tool({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "TypeName": "research",
                    "Role": "research-explorer",
                    "Prompt": "Survey backend architecture",
                    "Model": "flash",
                },
            }
        })
        self.assertEqual(res_ok.get("decision"), "allow")

        # Invalid TypeName at top-level
        res_invalid_type = self._run_pre_tool({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "TypeName": "custom-worker",
                    "Role": "dev-be",
                    "Prompt": "Implement feature",
                },
            }
        })
        self.assertEqual(res_invalid_type.get("decision"), "deny")
        self.assertIn("Native TypeName Contract Violation", res_invalid_type.get("reason", ""))

        # Invalid Model at top-level
        res_invalid_model = self._run_pre_tool({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "TypeName": "self",
                    "Role": "dev-be",
                    "Prompt": "allowed_files:\n  - a.py\nImplement",
                    "Model": "claude-sonnet-4",
                },
            }
        })
        self.assertEqual(res_invalid_model.get("decision"), "deny")
        self.assertIn("Native Model Contract Violation", res_invalid_model.get("reason", ""))

        # Prompt > 6000 chars at top-level
        res_long_prompt = self._run_pre_tool({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "TypeName": "research",
                    "Role": "research-explorer",
                    "Prompt": "z" * 6005,
                },
            }
        })
        self.assertEqual(res_long_prompt.get("decision"), "deny")
        self.assertIn("Pub/Sub Sparsification Invariant", res_long_prompt.get("reason", ""))

        # Builder without allowed_files at top-level
        res_no_lease = self._run_pre_tool({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "TypeName": "self",
                    "Role": "dev-be",
                    "Prompt": "Please fix server.py",
                },
            }
        })
        self.assertEqual(res_no_lease.get("decision"), "deny")
        self.assertIn("BMAD Story Shard Lease Invariant", res_no_lease.get("reason", ""))

        # Builder with allowed_files at top-level
        res_with_lease = self._run_pre_tool({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "TypeName": "self",
                    "Role": "dev-be",
                    "Prompt": "allowed_files:\n  - config/hooks/test.py\nFix bug",
                },
            }
        })
        self.assertEqual(res_with_lease.get("decision"), "allow")

    def test_send_message_6000_char_sparsification(self):
        """Fix 3b: send_message message length is capped at 6,000 characters."""
        res_ok = self._run_pre_tool({
            "toolCall": {
                "name": "send_message",
                "args": {
                    "Recipient": "agent-sub-1",
                    "Message": "Short progress update: tests passed.",
                },
            }
        })
        self.assertEqual(res_ok.get("decision"), "allow")

        res_boundary = self._run_pre_tool({
            "toolCall": {
                "name": "send_message",
                "args": {
                    "Recipient": "agent-sub-1",
                    "Message": "m" * 6000,
                },
            }
        })
        self.assertEqual(res_boundary.get("decision"), "allow")

        res_denied = self._run_pre_tool({
            "toolCall": {
                "name": "send_message",
                "args": {
                    "Recipient": "agent-sub-1",
                    "Message": "m" * 6001,
                },
            }
        })
        self.assertEqual(res_denied.get("decision"), "deny")
        self.assertIn("Pub/Sub Sparsification Invariant", res_denied.get("reason", ""))
        self.assertIn("6001 chars", res_denied.get("reason", ""))

    def test_slice_loop_breaker_parallel_turn_and_high_overlap(self):
        """Fix 4: Parallel reads in same turn do not false-positive; >= 80% overlap is blocked."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            for i in range(600):
                f.write(f"# line {i}\n")
            target_file = f.name

        try:
            # Parallel turn scenario: transcript has a single PLANNER_RESPONSE with TWO parallel slices
            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
                tf.write(json.dumps({
                    "type": "PLANNER_RESPONSE",
                    "tool_calls": [
                        {"name": "view_file", "args": {"AbsolutePath": target_file, "StartLine": 1, "EndLine": 100}},
                        {"name": "view_file", "args": {"AbsolutePath": target_file, "StartLine": 101, "EndLine": 200}},
                    ],
                }) + "\n")
                tf_path = tf.name

            try:
                # First parallel slice (1..100) -> must be allowed (NOT false-positived as duplicate slice)
                res_p1 = self._run_pre_tool({
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {"AbsolutePath": target_file, "StartLine": 1, "EndLine": 100},
                    },
                })
                self.assertEqual(res_p1.get("decision"), "allow")

                # Second parallel slice (101..200) -> must be allowed
                res_p2 = self._run_pre_tool({
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {"AbsolutePath": target_file, "StartLine": 101, "EndLine": 200},
                    },
                })
                self.assertEqual(res_p2.get("decision"), "allow")
            finally:
                if os.path.isfile(tf_path):
                    os.remove(tf_path)

            # High overlap scenario (>= 80% overlap with already read slice)
            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf2:
                # Turn 1: reads 100..250 (151 lines)
                tf2.write(json.dumps({
                    "type": "PLANNER_RESPONSE",
                    "tool_calls": [
                        {"name": "view_file", "args": {"AbsolutePath": target_file, "StartLine": 100, "EndLine": 250}},
                    ],
                }) + "\n")
                # User turn in between to commit turn 1
                tf2.write(json.dumps({"type": "USER_INPUT", "content": "continue"}) + "\n")
                # Turn 2: attempts 105..255 (151 lines, intersection 146 / 151 = 96.7% overlap)
                tf2.write(json.dumps({
                    "type": "PLANNER_RESPONSE",
                    "tool_calls": [
                        {"name": "view_file", "args": {"AbsolutePath": target_file, "StartLine": 105, "EndLine": 255}},
                    ],
                }) + "\n")
                tf2_path = tf2.name

            try:
                res_overlap = self._run_pre_tool({
                    "transcriptPath": tf2_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {"AbsolutePath": target_file, "StartLine": 105, "EndLine": 255},
                    },
                })
                self.assertEqual(res_overlap.get("decision"), "deny")
                self.assertIn("Slice Loop Breaker ACTIVATED", res_overlap.get("reason", ""))
                self.assertIn("duplicate slice loop", res_overlap.get("reason", ""))
            finally:
                if os.path.isfile(tf2_path):
                    os.remove(tf2_path)
        finally:
            if os.path.isfile(target_file):
                os.remove(target_file)

    def test_gradle_pty_progress_bar_flood_guard(self):
        """Fix 5: gradle/gradlew commands require --console=plain -q or quiet flags."""
        # Unbounded gradle commands -> denied
        for cmd in (
            "./gradlew assembleRelease",
            "gradle build",
            "./gradlew test",
            "/opt/gradle/bin/gradle check",
        ):
            res = self._run_pre_tool({
                "toolCall": {"name": "run_command", "args": {"CommandLine": cmd}},
            })
            self.assertEqual(res.get("decision"), "deny", f"Command '{cmd}' should be denied")
            self.assertIn("Unbounded `gradle`/`gradlew` PTY progress output detected", res.get("reason", ""))
            self.assertIn("--console=plain -q", res.get("reason", ""))

        # Bounded / quiet gradle commands -> allowed
        for cmd in (
            "./gradlew assembleRelease --console=plain -q",
            "gradle --quiet build",
            "./gradlew -q test",
            "./gradlew --console=plain test",
            "./gradlew --version",
            "gradle -v",
            "./gradlew --help",
            "./gradlew -h",
            "./gradlew --status",
            "./gradlew --stop",
            "./gradlew build | cat",
            "./gradlew assembleRelease > /tmp/build.log",
        ):
            res = self._run_pre_tool({
                "toolCall": {"name": "run_command", "args": {"CommandLine": cmd}},
            })
            self.assertEqual(res.get("decision"), "allow", f"Command '{cmd}' should be allowed")

    def test_subagent_model_pinning_and_force_ask_escalation_gate(self):
        """Subagent Model Pinning & force_ask Escalation Gate across invoke_subagent and run_command."""
        # 1. Baseline allow (self with inherit, research-explorer with flash, diff-helper with flash_lite)
        res_self_ok = self._run_pre_tool({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "TypeName": "self",
                    "Role": "dev-be",
                    "Prompt": "allowed_files:\n  - a.py\nImplement feature",
                    "Model": "inherit",
                },
            }
        })
        self.assertEqual(res_self_ok.get("decision"), "allow")
        self.assertNotIn("overwrite", res_self_ok)

        res_diff_ok = self._run_pre_tool({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "TypeName": "research",
                    "Role": "diff-helper",
                    "Prompt": "Summarize diff",
                    "Model": "flash_lite",
                },
            }
        })
        self.assertEqual(res_diff_ok.get("decision"), "allow")

        # 2. Model: "pro" on self role -> force_ask
        res_pro = self._run_pre_tool({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "TypeName": "self",
                    "Role": "dev-be",
                    "Prompt": "allowed_files:\n  - a.py\nImplement feature",
                    "Model": "pro",
                },
            }
        })
        self.assertEqual(res_pro.get("decision"), "force_ask")
        self.assertIn("Subagent Model Escalation Gate", res_pro.get("reason", ""))
        self.assertIn("baseline model 'inherit'", res_pro.get("reason", ""))
        self.assertIn("stronger model 'pro'", res_pro.get("reason", ""))

        # 3. research-explorer with inherit or pro -> force_ask
        for esc_model in ("inherit", "pro"):
            res_exp_esc = self._run_pre_tool({
                "toolCall": {
                    "name": "invoke_subagent",
                    "args": {
                        "TypeName": "research",
                        "Role": "research-explorer",
                        "Prompt": "Explore repo",
                        "Model": esc_model,
                    },
                }
            })
            self.assertEqual(res_exp_esc.get("decision"), "force_ask")
            self.assertIn("baseline model 'flash'", res_exp_esc.get("reason", ""))
            self.assertIn(f"stronger model '{esc_model}'", res_exp_esc.get("reason", ""))

        # 4. diff-helper with flash -> force_ask
        res_diff_esc = self._run_pre_tool({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "TypeName": "research",
                    "Role": "diff-helper",
                    "Prompt": "Summarize diff",
                    "Model": "flash",
                },
            }
        })
        self.assertEqual(res_diff_esc.get("decision"), "force_ask")
        self.assertIn("baseline model 'flash_lite'", res_diff_esc.get("reason", ""))
        self.assertIn("stronger model 'flash'", res_diff_esc.get("reason", ""))

        # 5. Top-level research with omitted Model -> overwrite: {"Model": "flash"}
        res_top_omit = self._run_pre_tool({
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "TypeName": "research",
                    "Role": "research-explorer",
                    "Prompt": "Explore repo without explicit Model",
                },
            }
        })
        self.assertEqual(res_top_omit.get("decision"), "allow")
        self.assertEqual(res_top_omit.get("overwrite"), {"Model": "flash"})

        # 6. agy --model gemini-4-argon-high in run_command -> force_ask
        for cli_cmd in (
            "agy --model gemini-4-argon-high --effort xhigh 'audit code'",
            "agy --model=gemini-4-argon-high 'run review'",
        ):
            res_cli_esc = self._run_pre_tool({
                "toolCall": {"name": "run_command", "args": {"CommandLine": cli_cmd}},
            })
            self.assertEqual(res_cli_esc.get("decision"), "force_ask")
            self.assertIn("Subagent CLI Model Escalation Gate", res_cli_esc.get("reason", ""))
            self.assertIn("gemini-4-argon-high", res_cli_esc.get("reason", ""))

    def test_hooks_json_lifecycle_and_matcher_closure(self):
        """Verify config/hooks.json moves herdr to SessionStart, adds --session-start, and expands matchers."""
        hooks_cfg_path = REPO_ROOT / "config" / "hooks.json"
        with open(hooks_cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        self.assertIn("SessionStart", cfg.get("herdr", {}))
        self.assertNotIn("PreInvocation", cfg.get("herdr", {}))

        intake = cfg.get("intake-grounding-gate", {})
        self.assertIn("PreInvocation", intake)
        self.assertIn("SessionStart", intake)
        ss_cmds = [h.get("command", "") for h in intake.get("SessionStart", [])]
        self.assertTrue(any("--session-start" in c for c in ss_cmds))

        pre_matcher = cfg["safety-and-loop-gate"]["PreToolUse"][0]["matcher"]
        for tok in ("schedule", "run_workflow", "define_subagent", "mcp_.*"):
            self.assertIn(tok, pre_matcher)

        post_matcher = cfg["syntax-smoke-gate"]["PostToolUse"][0]["matcher"]
        for tok in ("call_mcp_tool", "mcp_.*"):
            self.assertIn(tok, post_matcher)

    def test_system_sdk_step0_skip_and_subagent_detection(self):
        """Verify _get_first_transcript_step skips SYSTEM_SDK/grounding anchors and _is_subagent_conversation is fail-closed."""
        # Minimal unit-test payload -> False
        self.assertFalse(pre_tool_use_hook._is_subagent_conversation({"toolCall": {"name": "run_command"}}))

        # Positive subagent metadata -> True
        self.assertTrue(pre_tool_use_hook._is_subagent_conversation({"is_subagent": True}))
        self.assertTrue(pre_tool_use_hook._is_subagent_conversation({"subagentRole": "dev-be"}))
        self.assertTrue(pre_tool_use_hook._is_subagent_conversation({"parentConversationId": "parent-123"}))
        self.assertTrue(pre_tool_use_hook._is_subagent_conversation({"agentRole": "research-explorer"}))
        self.assertFalse(pre_tool_use_hook._is_subagent_conversation({"agentRole": "pm"}))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf_root:
            tf_root.write(json.dumps({
                "step_index": 0,
                "source": "SYSTEM_SDK",
                "type": "SYSTEM_MESSAGE",
                "content": "[Session Grounding Anchor]\nProject Slug: demo",
            }) + "\n")
            tf_root.write(json.dumps({
                "step_index": 1,
                "source": "USER_EXPLICIT",
                "type": "USER_INPUT",
                "content": "Fix bug in app.py",
            }) + "\n")
            root_path = tf_root.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf_sub:
            tf_sub.write(json.dumps({
                "step_index": 0,
                "source": "SYSTEM_SDK",
                "type": "SYSTEM_MESSAGE",
                "content": "[Session Grounding Anchor]\nProject Slug: demo",
            }) + "\n")
            tf_sub.write(json.dumps({
                "step_index": 1,
                "source": "SYSTEM",
                "type": "SYSTEM_MESSAGE",
                "content": "Execute Shard\nRole: dev-be\nallowed_files:\n- allowed.py",
            }) + "\n")
            sub_path = tf_sub.name

        try:
            root_payload = {"transcriptPath": root_path}
            first_root = pre_tool_use_hook._get_first_transcript_step(root_payload)
            self.assertIsNotNone(first_root)
            self.assertEqual(first_root.get("type"), "USER_INPUT")
            self.assertFalse(pre_tool_use_hook._is_subagent_conversation(root_payload))
            is_nb, role_lbl = pre_tool_use_hook._detect_non_builder_session(root_payload)
            self.assertTrue(is_nb)
            self.assertEqual(role_lbl, "Root Orchestrator (PM)")

            sub_payload = {"transcriptPath": sub_path}
            first_sub = pre_tool_use_hook._get_first_transcript_step(sub_payload)
            self.assertIsNotNone(first_sub)
            self.assertEqual(first_sub.get("type"), "SYSTEM_MESSAGE")
            self.assertIn("allowed.py", first_sub.get("content", ""))
            self.assertTrue(pre_tool_use_hook._is_subagent_conversation(sub_payload))
        finally:
            for p in (root_path, sub_path):
                if os.path.isfile(p):
                    os.remove(p)

    def test_subagent_interactive_gate_rewritten_to_deny(self):
        """Verify ask/force_ask decisions are rewritten to deny for subagents so background subagents never hang."""
        res_sub = self._run_pre_tool({
            "subagentRole": "dev-be",
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": "rm -rf /home/heocop/test"},
            },
        })
        self.assertEqual(res_sub.get("decision"), "deny")
        self.assertIn("Subagent Interactive Gate Blocked", res_sub.get("reason", ""))

    def test_schedule_is_daemon_force_ask(self):
        """Verify schedule with IsDaemon=True triggers force_ask (and deny for subagents)."""
        res_daemon = self._run_pre_tool({
            "toolCall": {
                "name": "schedule",
                "args": {"CronExpression": "*/10 * * * *", "Prompt": "Run health check", "IsDaemon": True},
            },
        })
        self.assertEqual(res_daemon.get("decision"), "force_ask")
        self.assertIn("Standing Daemon Schedule Gate", res_daemon.get("reason", ""))

        res_normal = self._run_pre_tool({
            "toolCall": {
                "name": "schedule",
                "args": {"CronExpression": "*/10 * * * *", "Prompt": "Run health check", "IsDaemon": False},
            },
        })
        self.assertEqual(res_normal.get("decision"), "allow")

    def test_run_workflow_define_subagent_and_mcp_tool_gates(self):
        """Verify _handle_run_workflow, _handle_define_subagent, _handle_mcp_tool, and _safe_shallow_overwrite."""
        # 1. run_workflow parallel > 6 -> deny; <= 6 -> allow
        res_wf_deny = self._run_pre_tool({
            "toolCall": {
                "name": "run_workflow",
                "args": {"Script": "parallel([a, b, c, d, e, f, g])"},
            },
        })
        self.assertEqual(res_wf_deny.get("decision"), "deny")
        self.assertIn("Workflow Concurrency Budget Violation", res_wf_deny.get("reason", ""))

        res_wf_ok = self._run_pre_tool({
            "toolCall": {
                "name": "run_workflow",
                "args": {"Script": "parallel([a, b, c, d])"},
            },
        })
        self.assertEqual(res_wf_ok.get("decision"), "allow")

        # 2. run_workflow model escalation -> force_ask
        res_wf_esc = self._run_pre_tool({
            "toolCall": {
                "name": "run_workflow",
                "args": {"Script": "agent(prompt='audit', model='gemini-4-argon-high')"},
            },
        })
        self.assertEqual(res_wf_esc.get("decision"), "force_ask")
        self.assertIn("Workflow Model Escalation Gate", res_wf_esc.get("reason", ""))

        # 3. run_workflow PM source mutation -> deny
        res_wf_pm = self._run_pre_tool({
            "agentRole": "pm",
            "toolCall": {
                "name": "run_workflow",
                "args": {"Script": "write_file('src/index.ts', 'console.log(1)')"},
            },
        })
        self.assertEqual(res_wf_pm.get("decision"), "deny")
        self.assertIn("Role Isolation Workflow Guard", res_wf_pm.get("reason", ""))

        # 4. define_subagent SystemPrompt > 8000 -> deny; subagent recursion -> deny
        res_def_big = self._run_pre_tool({
            "toolCall": {
                "name": "define_subagent",
                "args": {"Name": "custom", "Description": "d", "SystemPrompt": "x" * 8001},
            },
        })
        self.assertEqual(res_def_big.get("decision"), "deny")
        self.assertIn("8,000-character ceiling", res_def_big.get("reason", ""))

        res_def_sub = self._run_pre_tool({
            "subagentRole": "dev-be",
            "toolCall": {
                "name": "define_subagent",
                "args": {"Name": "nested", "Description": "d", "SystemPrompt": "short"},
            },
        })
        self.assertEqual(res_def_sub.get("decision"), "deny")
        self.assertIn("Subagent Recursion Depth Violation", res_def_sub.get("reason", ""))

        # 5. Multi-underscore mcp_* and call_mcp_tool on read-only explorer subagent
        for mut_tool in (
            {"name": "mcp_codex_knowledge_memory_store", "args": {"slug": "s", "key": "k", "value": "v"}},
            {"name": "mcp_context_health_commit_context_ledger", "args": {"milestone": "m"}},
            {"name": "call_mcp_tool", "args": {"ServerName": "codex_knowledge", "ToolName": "vault_write"}},
            {"name": "mcp_custom_create_record", "args": {}},
        ):
            res_mcp_deny = self._run_pre_tool({
                "subagentRole": "research-explorer",
                "toolCall": mut_tool,
            })
            self.assertEqual(res_mcp_deny.get("decision"), "deny", f"Expected deny for {mut_tool['name']}")
            self.assertIn("Read-Only Subagent MCP Mutation Lock", res_mcp_deny.get("reason", ""))

        res_mcp_ro_ok = self._run_pre_tool({
            "subagentRole": "research-explorer",
            "toolCall": {
                "name": "mcp_codegraph_symbol_lookup",
                "args": {"root": "/repo", "query": "main"},
            },
        })
        self.assertEqual(res_mcp_ro_ok.get("decision"), "allow")

        res_mcp_builder_ok = self._run_pre_tool({
            "subagentRole": "dev-be",
            "toolCall": {
                "name": "mcp_codex_knowledge_memory_store",
                "args": {"slug": "s", "key": "k", "value": "v"},
            },
        })
        self.assertEqual(res_mcp_builder_ok.get("decision"), "allow")

        # 6. _safe_shallow_overwrite preserves nested sibling keys
        orig = {"ServerName": "codegraph", "Arguments": {"root": "/repo", "query": "foo"}}
        merged = pre_tool_use_hook._safe_shallow_overwrite(orig, {"Arguments": {"limit": 20}})
        self.assertEqual(merged, {"Arguments": {"root": "/repo", "query": "foo", "limit": 20}})


if __name__ == "__main__":
    unittest.main()


