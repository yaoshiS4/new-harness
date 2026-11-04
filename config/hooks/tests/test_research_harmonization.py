"""Unit tests for Research Harmonization Upgrades (Shard A).

Covers:
- Upgrade 2: Anti-Process & Pipe Exit-Code Swallowing Guard (pre_tool_use_hook.py)
- Upgrade 3: CATCH Reward-Hacking & Test Tampering Defense (pre_tool_use_hook.py)
- Upgrade 4: PostToolUse Structured Feedback & Exception Memory (post_tool_use_hook.py)
- Upgrade 5: Agentic IR Reconnaissance Pre-Condition (pre_tool_use_hook.py)
- Upgrade 7: AdaSearch Epistemic Uncertainty Directive (pre_tool_use_hook.py)
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add hooks directory to path for direct imports
HOOKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

import post_tool_use_hook
import pre_tool_use_hook


class TestUpgrade2ProcessAndPipeExitCodeGuards(unittest.TestCase):
    def test_verification_command_exit_masking_denied(self) -> None:
        blocked_commands = [
            "pytest tests/test_foo.py || true",
            "pytest tests/test_foo.py || :",
            "pytest tests/test_foo.py || echo 'swallowed'",
            "cargo test --bin foo || true",
            "tsc --noEmit || true",
            "ruff check . || :",
            "verify-oracle.sh || true",
            "npm test || true",
        ]
        for cmd in blocked_commands:
            payload = {"conversationId": "test_conv"}
            args = {"CommandLine": cmd}
            res = pre_tool_use_hook._handle_run_command(args, payload)
            self.assertEqual(
                res.get("decision"),
                "deny",
                f"Command '{cmd}' should have been denied for exit-code masking.",
            )
            self.assertIn("Process Exit-Code Masking Invariant", res.get("reason", ""))

    def test_non_verification_command_exit_masking_allowed(self) -> None:
        cmd = "echo 'hello' || true"
        payload = {"conversationId": "test_conv"}
        args = {"CommandLine": cmd}
        res = pre_tool_use_hook._handle_run_command(args, payload)
        self.assertEqual(res.get("decision"), "allow")

    def test_runner_as_argument_to_search_commands_allowed(self) -> None:
        allowed_argument_commands = [
            "rg tsc src/ | head -n 50",
            "fd pytest src/ || true",
            "git log --grep=pytest || true",
            "echo pytest || true",
        ]
        for cmd in allowed_argument_commands:
            payload = {"conversationId": "test_conv"}
            args = {"CommandLine": cmd}
            res = pre_tool_use_hook._handle_run_command(args, payload)
            self.assertEqual(
                res.get("decision"),
                "allow",
                f"Command '{cmd}' should have been allowed since runner is merely an argument.",
            )

    def test_verification_command_pipe_without_pipefail_denied(self) -> None:
        blocked_pipes = [
            "pytest tests/test_foo.py | head -n 30",
            "pytest tests/test_foo.py | tail -n 20",
            "cargo test | tee /tmp/test.log",
            "tsc --noEmit | head -n 10",
        ]
        for cmd in blocked_pipes:
            payload = {"conversationId": "test_conv"}
            args = {"CommandLine": cmd}
            res = pre_tool_use_hook._handle_run_command(args, payload)
            self.assertEqual(
                res.get("decision"),
                "deny",
                f"Command '{cmd}' should have been denied for pipe without pipefail.",
            )
            self.assertIn("Process Pipe Exit-Code Swallowing Guard", res.get("reason", ""))
            self.assertIn("set -o pipefail", res.get("reason", ""))

    def test_verification_command_pipe_with_pipefail_allowed(self) -> None:
        allowed_pipes = [
            "set -o pipefail; pytest tests/test_foo.py | head -n 30",
            "set -eo pipefail; cargo test | tail -n 20",
            "set -o pipefail; tsc --noEmit | tee /tmp/tsc.log",
        ]
        for cmd in allowed_pipes:
            payload = {"conversationId": "test_conv"}
            args = {"CommandLine": cmd}
            res = pre_tool_use_hook._handle_run_command(args, payload)
            self.assertEqual(
                res.get("decision"),
                "allow",
                f"Command '{cmd}' should have been allowed with pipefail.",
            )


class TestUpgrade3CatchTamperingAndSuppressionDefense(unittest.TestCase):
    def test_test_skip_re_expanded(self) -> None:
        samples = [
            "@pytest.mark.skip",
            "@pytest.mark.xfail",
            "pytest.xfail('flaky')",
            "@unittest.skip('not ready')",
            "@unittest.expectedFailure",
            "test.todo('future test')",
            "it.todo('future test')",
            "describe.skip('group')",
            "xit('disabled')",
        ]
        for s in samples:
            self.assertTrue(
                bool(pre_tool_use_hook._TEST_SKIP_RE.search(s)),
                f"Pattern '{s}' should be matched by _TEST_SKIP_RE",
            )

    def test_zero_exit_spoofing_in_test_files_denied(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix="_test.py", delete=False) as tf:
            tf.write("def test_something():\n    assert 1 == 1\n")
            test_file = tf.name

        try:
            payload = {
                "conversationId": "test_conv",
                "transcript": [{"type": "SYSTEM_MESSAGE", "content": "Role: dev-be"}],
            }
            args = {
                "Path": test_file,
                "TargetContent": "def test_something():\n    assert 1 == 1\n",
                "ReplacementContent": "def test_something():\n    import sys; sys.exit(0)\n    assert 1 == 1\n",
            }
            res = pre_tool_use_hook._handle_file_mutation("replace_file_content", args, payload)
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Test-Immutability Lock (CATCH Execution Interference)", res.get("reason", ""))
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_suppression_injection_in_code_and_tests_denied(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".ts", delete=False) as tf:
            tf.write("const a: number = 1;\n")
            code_file = tf.name

        try:
            payload = {
                "conversationId": "test_conv",
                "transcript": [{"type": "SYSTEM_MESSAGE", "content": "Role: dev-fe"}],
            }
            args = {
                "Path": code_file,
                "TargetContent": "const a: number = 1;\n",
                "ReplacementContent": "// @ts-ignore\nconst a: number = 1;\n",
            }
            res = pre_tool_use_hook._handle_file_mutation("replace_file_content", args, payload)
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Specification-Gaming Lock", res.get("reason", ""))
        finally:
            if os.path.exists(code_file):
                os.remove(code_file)

    def test_suppression_injection_on_append_denied(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write("x = 1\n")
            py_file = tf.name

        try:
            payload = {
                "conversationId": "test_conv",
                "transcript": [{"type": "SYSTEM_MESSAGE", "content": "Role: dev-be"}],
            }
            args = {
                "Path": py_file,
                "Append": True,
                "Content": "# type: ignore\ny = 2\n",
            }
            res = pre_tool_use_hook._handle_file_mutation("write_file", args, payload)
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Specification-Gaming Lock", res.get("reason", ""))
        finally:
            if os.path.exists(py_file):
                os.remove(py_file)

    def test_suppression_injection_on_multi_replace_denied(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".ts", delete=False) as tf:
            tf.write("const a = 1;\nconst b = 2;\n")
            ts_file = tf.name

        try:
            payload = {
                "conversationId": "test_conv",
                "transcript": [{"type": "SYSTEM_MESSAGE", "content": "Role: dev-fe"}],
            }
            args = {
                "Path": ts_file,
                "ReplacementChunks": [
                    {
                        "Target": "const a = 1;",
                        "Replacement": "// @ts-ignore\nconst a = 1;",
                    }
                ],
            }
            res = pre_tool_use_hook._handle_file_mutation("multi_replace_file_content", args, payload)
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Specification-Gaming Lock", res.get("reason", ""))
        finally:
            if os.path.exists(ts_file):
                os.remove(ts_file)


class TestUpgrade4PostToolUseStructuredFeedback(unittest.TestCase):
    def test_extract_structured_command_feedback_python_traceback(self) -> None:
        output = """Traceback (most recent call last):
  File "src/server.py", line 42, in handle_request
    raise ValueError("invalid request payload")
ValueError: invalid request payload
"""
        feedback = post_tool_use_hook._extract_structured_command_feedback(output)
        failures = feedback.get("failures", [])
        self.assertGreaterEqual(len(failures), 1)
        self.assertEqual(failures[0]["file"], "src/server.py")
        self.assertEqual(failures[0]["line"], 42)
        self.assertEqual(failures[0]["error_type"], "ValueError")
        self.assertEqual(failures[0]["message"], "invalid request payload")

    def test_extract_structured_command_feedback_pytest(self) -> None:
        output = """FAILED tests/test_math.py::test_sum - AssertionError: assert 1 == 2"""
        feedback = post_tool_use_hook._extract_structured_command_feedback(output)
        failures = feedback.get("failures", [])
        self.assertGreaterEqual(len(failures), 1)
        self.assertEqual(failures[0]["file"], "tests/test_math.py")
        self.assertEqual(failures[0]["error_type"], "AssertionError")
        self.assertEqual(failures[0]["observed"], "1")
        self.assertEqual(failures[0]["expected"], "2")

    def test_extract_structured_command_feedback_typescript(self) -> None:
        output = """src/components/Header.tsx:18:5 - error TS2305: Module '"./types"' has no exported member 'User'."""
        feedback = post_tool_use_hook._extract_structured_command_feedback(output)
        failures = feedback.get("failures", [])
        self.assertGreaterEqual(len(failures), 1)
        self.assertEqual(failures[0]["file"], "src/components/Header.tsx")
        self.assertEqual(failures[0]["line"], 18)
        self.assertEqual(failures[0]["error_type"], "TS2305")

    def test_extract_structured_command_feedback_rust(self) -> None:
        output = """error[E0425]: cannot find value `foo` in this scope
  --> src/main.rs:12:9"""
        feedback = post_tool_use_hook._extract_structured_command_feedback(output)
        failures = feedback.get("failures", [])
        self.assertGreaterEqual(len(failures), 1)
        self.assertEqual(failures[0]["file"], "src/main.rs")
        self.assertEqual(failures[0]["line"], 12)
        self.assertEqual(failures[0]["error_type"], "E0425")

    def test_post_run_command_writes_feedback_file(self) -> None:
        conv_id = "test_feedback_conv_123"
        target_feedback = f"/tmp/.antigravity_structured_feedback_{conv_id}.json"
        if os.path.exists(target_feedback):
            os.remove(target_feedback)

        payload = {
            "conversationId": conv_id,
            "toolCall": {"name": "run_command", "args": {"CommandLine": "pytest"}},
            "output": "FAILED test_sample.py::test_fn - AssertionError: assert 5 == 10",
        }
        post_tool_use_hook._handle_post_run_command(payload)
        self.assertTrue(os.path.exists(target_feedback))
        try:
            with open(target_feedback, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data.get("conversation_id"), conv_id)
            self.assertEqual(data.get("error_type"), "AssertionError")
            self.assertEqual(data.get("observed"), "5")
            self.assertEqual(data.get("expected"), "10")
        finally:
            if os.path.exists(target_feedback):
                os.remove(target_feedback)

    def test_clean_run_command_unlinks_stale_feedback_file(self) -> None:
        conv_id = "test_clean_conv_456"
        target_feedback = f"/tmp/.antigravity_structured_feedback_{conv_id}.json"
        with open(target_feedback, "w", encoding="utf-8") as f:
            f.write(json.dumps({"stale": True, "error_type": "AssertionError"}))

        try:
            payload = {
                "conversationId": conv_id,
                "toolCall": {"name": "run_command", "args": {"CommandLine": "pytest"}},
                "output": "1 passed in 0.05s\nCommand exited with code 0.",
            }
            post_tool_use_hook._handle_post_run_command(payload)
            self.assertFalse(
                os.path.exists(target_feedback),
                "Clean command execution must unlink stale feedback file.",
            )
        finally:
            if os.path.exists(target_feedback):
                os.remove(target_feedback)


class TestUpgrade5AgenticIRReconnaissancePreCondition(unittest.TestCase):
    def test_implementation_plan_blocked_without_prior_recon(self) -> None:
        plan_path = "/tmp/test_workspace_recon/implementation_plan.md"
        if os.path.exists(plan_path):
            os.remove(plan_path)

        old_env = os.environ.get("ANTIGRAVITY_ENFORCE_RECON_GATE")
        try:
            os.environ["ANTIGRAVITY_ENFORCE_RECON_GATE"] = "1"
            payload = {
                "conversationId": "test_recon_conv",
                "transcript": [
                    {
                        "type": "USER_INPUT",
                        "content": "Please plan our new feature.",
                    },
                    {
                        "type": "PLANNER_RESPONSE",
                        "tool_calls": [
                            {"name": "write_file", "args": {"Path": plan_path, "Content": "# Plan"}}
                        ],
                    },
                ],
            }
            args = {"Path": plan_path, "Content": "# Plan"}
            res = pre_tool_use_hook._handle_file_mutation("write_file", args, payload)
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Agentic IR Reconnaissance Pre-Condition", res.get("reason", ""))
        finally:
            if old_env is None:
                os.environ.pop("ANTIGRAVITY_ENFORCE_RECON_GATE", None)
            else:
                os.environ["ANTIGRAVITY_ENFORCE_RECON_GATE"] = old_env
            if os.path.exists(plan_path):
                os.remove(plan_path)

    def test_implementation_plan_allowed_after_recon(self) -> None:
        plan_path = "/tmp/test_workspace_recon/implementation_plan.md"
        if os.path.exists(plan_path):
            os.remove(plan_path)

        old_env = os.environ.get("ANTIGRAVITY_ENFORCE_RECON_GATE")
        try:
            os.environ["ANTIGRAVITY_ENFORCE_RECON_GATE"] = "1"
            payload = {
                "conversationId": "test_recon_conv",
                "transcript": [
                    {
                        "type": "USER_INPUT",
                        "content": "Please plan our new feature.",
                    },
                    {
                        "type": "PLANNER_RESPONSE",
                        "tool_calls": [
                            {"name": "read_file", "args": {"Path": "/src/main.py"}}
                        ],
                    },
                ],
            }
            args = {"Path": plan_path, "Content": "# Plan"}
            res = pre_tool_use_hook._handle_file_mutation("write_file", args, payload)
            self.assertEqual(res.get("decision"), "allow")
        finally:
            if old_env is None:
                os.environ.pop("ANTIGRAVITY_ENFORCE_RECON_GATE", None)
            else:
                os.environ["ANTIGRAVITY_ENFORCE_RECON_GATE"] = old_env
            if os.path.exists(plan_path):
                os.remove(plan_path)

    def test_transcript_null_function_safety(self) -> None:
        plan_path = "/tmp/test_workspace_recon/implementation_plan.md"
        if os.path.exists(plan_path):
            os.remove(plan_path)

        old_env = os.environ.get("ANTIGRAVITY_ENFORCE_RECON_GATE")
        try:
            os.environ["ANTIGRAVITY_ENFORCE_RECON_GATE"] = "1"
            payload = {
                "conversationId": "test_recon_conv",
                "transcript": [
                    {
                        "type": "PLANNER_RESPONSE",
                        "tool_calls": [
                            {"name": None, "function": None, "args": {}},
                            {"name": "read_file", "args": {"Path": "/src/main.py"}},
                        ],
                    },
                ],
            }
            args = {"Path": plan_path, "Content": "# Plan"}
            res = pre_tool_use_hook._handle_file_mutation("write_file", args, payload)
            self.assertEqual(res.get("decision"), "allow")
        finally:
            if old_env is None:
                os.environ.pop("ANTIGRAVITY_ENFORCE_RECON_GATE", None)
            else:
                os.environ["ANTIGRAVITY_ENFORCE_RECON_GATE"] = old_env
            if os.path.exists(plan_path):
                os.remove(plan_path)


class TestUpgrade7AdaSearchEpistemicUncertainty(unittest.TestCase):
    def test_epistemic_uncertainty_error_detection(self) -> None:
        self.assertIsNotNone(pre_tool_use_hook._detect_epistemic_uncertainty_error("ModuleNotFoundError: No module named 'jwt'"))
        self.assertIsNotNone(pre_tool_use_hook._detect_epistemic_uncertainty_error("ImportError: cannot import name 'load_yaml'"))
        self.assertIsNotNone(pre_tool_use_hook._detect_epistemic_uncertainty_error("error TS2305: Module 'foo' has no exported member 'bar'"))
        self.assertIsNotNone(pre_tool_use_hook._detect_epistemic_uncertainty_error("Cannot find module 'express'"))
        self.assertIsNone(pre_tool_use_hook._detect_epistemic_uncertainty_error("SyntaxError: invalid syntax"))

    def test_error_stagnation_appends_adasearch_directive_on_epistemic_error(self) -> None:
        conv_id = "test_adasearch_conv"
        ledger_path = os.path.join(tempfile.gettempdir(), f".antigravity_err_sig_{conv_id}.json")
        try:
            dummy_sig = "dummy_epistemic_sig_123"
            pre_tool_use_hook._atomic_json_write(ledger_path, {
                "signatures": [dummy_sig, dummy_sig, dummy_sig],
                "last_error": "ModuleNotFoundError: No module named 'anthropic'",
            })
            payload = {"conversationId": conv_id}
            res = pre_tool_use_hook._check_error_stagnation_circuit_breaker(payload, "run_command", {"CommandLine": "pytest"})
            self.assertIsNotNone(res)
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("AdaSearch Epistemic Uncertainty Trigger", res.get("reason", ""))
            self.assertIn("context7", res.get("reason", ""))
        finally:
            if os.path.exists(ledger_path):
                os.remove(ledger_path)


if __name__ == "__main__":
    unittest.main()
