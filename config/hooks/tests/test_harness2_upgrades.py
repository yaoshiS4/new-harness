"""Unit tests for Antigravity Harness² recursive architecture and mechanical upgrades.

Covers:
1. Debugger Test-Assertion Lock (Fix-The-Code-Not-The-Test invariant, existing vs new test files).
2. Hook Immunity Guard (prevents unauthorized roles from mutating system hooks).
3. Mechanical Harness Tree Validator (validate-harness-tree.py checks 1-4).
4. Cue-Matched memory retrieval and SkillBank indexing.
5. Level-1 Recursive PPC Engine (recursive-ppc-engine.py and KEEP_BASE default).
6. Level-2 Experience Reflector (reflect-experience.py and NO_ENTRY confounder gate).
"""

from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add hooks directory to path for direct imports
HOOKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

SCRIPTS_DIR = os.path.abspath(os.path.join(HOOKS_DIR, "..", "..", "antigravity", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def _resolve_script_path(script_name: str) -> str:
    repo_p = os.path.join(SCRIPTS_DIR, script_name)
    if os.path.isfile(repo_p):
        return repo_p
    gemini_p = os.path.expanduser(f"~/.gemini/antigravity/scripts/{script_name}")
    return gemini_p

import io
from unittest.mock import patch
import pre_tool_use_hook
from pre_tool_use_hook import (
    _extract_session_role,
    _handle_file_mutation,
    _is_test_file_path,
)

import importlib.util

vht_path = os.path.join(SCRIPTS_DIR, "validate-harness-tree.py")
vht_spec = importlib.util.spec_from_file_location("validate_harness_tree", vht_path)
vht = importlib.util.module_from_spec(vht_spec)
vht_spec.loader.exec_module(vht)


class TestDebuggerTestAssertionLock(unittest.TestCase):
    """Tests the Fix-The-Code-Not-The-Test Debugger Test-Assertion Lock."""

    def test_is_test_file_path_matches_all_supported_patterns(self) -> None:
        positives = [
            "test_feature.py",
            "tests/test_harness.py",
            "/repo/src/calc_test.py",
            "calculator.test.ts",
            "components/button.test.tsx",
            "utils.test.js",
            "components/card.spec.ts",
            "views/dashboard.spec.tsx",
            "api/handler.spec.js",
            "server_test.go",
            "engine_test.rs",
            "/repo/src/__tests__/utils.ts",
            "__tests__/helper.js",
            "/home/user/project/__tests__/nested/test.js",
        ]
        for p in positives:
            self.assertTrue(_is_test_file_path(p), f"Should match test path: {p}")

        negatives = [
            "main.py",
            "calculator.ts",
            "components/button.tsx",
            "utils.js",
            "server.go",
            "engine.rs",
            "README.md",
            "package.json",
            "tests/conftest.py",
        ]
        for p in negatives:
            self.assertFalse(_is_test_file_path(p), f"Should NOT match test path: {p}")

    def test_debugger_blocked_from_mutating_existing_test_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_sample.py")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("def test_ok(): assert True\n")

            payload = {
                "role": "debugger",
                "workspacePaths": [tmpdir],
            }
            args = {"TargetFile": test_file}
            result = _handle_file_mutation("replace_file_content", args, payload)
            self.assertEqual(result.get("decision"), "deny")
            self.assertIn("Fix-The-Code-Not-The-Test Invariant", result.get("reason", ""))
            self.assertIn("debugger", result.get("reason", ""))

    def test_debugger_blocked_via_transcript_system_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "calculator.test.ts")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("test('add', () => {});\n")

            payload = {
                "transcript": [
                    {
                        "type": "SYSTEM_MESSAGE",
                        "content": 'Execute Shard 1. Role: "debugger"\nallowed_files:\n- calculator.test.ts',
                    }
                ],
                "workspacePaths": [tmpdir],
            }
            args = {"TargetFile": test_file}
            result = _handle_file_mutation("replace_file_content", args, payload)
            self.assertEqual(result.get("decision"), "deny")
            self.assertIn("Fix-The-Code-Not-The-Test Invariant", result.get("reason", ""))

    def test_debugger_allowed_to_create_new_test_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            new_test_file = os.path.join(tmpdir, "test_brand_new.py")
            # Ensure file does not exist on disk
            if os.path.exists(new_test_file):
                os.unlink(new_test_file)

            payload = {
                "role": "debugger",
                "workspacePaths": [tmpdir],
            }
            args = {
                "TargetFile": new_test_file,
                "CodeContent": "def test_new(): pass\n",
                "Overwrite": False,
                "Description": "New test file",
            }
            result = _handle_file_mutation("write_to_file", args, payload)
            # The Debugger Test-Assertion Lock only blocks *existing* test files
            # (Fix-The-Code-Not-The-Test prevents weakening existing tests)
            reason = result.get("reason", "")
            self.assertNotIn("Fix-The-Code-Not-The-Test Invariant", reason)

    def test_fix_code_only_env_blocks_any_role_from_mutating_existing_test(self) -> None:
        old_val = os.environ.get("FIX_CODE_ONLY")
        try:
            os.environ["FIX_CODE_ONLY"] = "1"
            with tempfile.TemporaryDirectory() as tmpdir:
                test_file = os.path.join(tmpdir, "test_core.py")
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write("def test_core(): pass\n")

                payload = {
                    "role": "dev-be",
                    "workspacePaths": [tmpdir],
                }
                args = {"TargetFile": test_file}
                result = _handle_file_mutation("replace_file_content", args, payload)
                self.assertEqual(result.get("decision"), "deny")
                self.assertIn("Fix-The-Code-Not-The-Test Invariant", result.get("reason", ""))
        finally:
            if old_val is None:
                os.environ.pop("FIX_CODE_ONLY", None)
            else:
                os.environ["FIX_CODE_ONLY"] = old_val

    def test_dev_be_allowed_to_mutate_existing_test_without_fix_code_only(self) -> None:
        old_val = os.environ.get("FIX_CODE_ONLY")
        try:
            os.environ.pop("FIX_CODE_ONLY", None)
            with tempfile.TemporaryDirectory() as tmpdir:
                test_file = os.path.join(tmpdir, "test_dev_be.py")
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write("def test_be(): pass\n")

                payload = {
                    "role": "dev-be",
                    "workspacePaths": [tmpdir],
                }
                args = {"TargetFile": test_file}
                result = _handle_file_mutation("replace_file_content", args, payload)
                reason = result.get("reason", "")
                self.assertNotIn("Fix-The-Code-Not-The-Test Invariant", reason)
        finally:
            if old_val is not None:
                os.environ["FIX_CODE_ONLY"] = old_val

    def test_dev_be_blocked_from_deleting_existing_assertions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_dev_be.py")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("def test_be():\n    assert 1 == 1\n    expect(x).toBe(2)\n")

            payload = {
                "role": "dev-be",
                "workspacePaths": [tmpdir],
            }
            # Attempt to delete assertion
            args = {
                "TargetFile": test_file,
                "Target": "    assert 1 == 1\n    expect(x).toBe(2)\n",
                "Replacement": "    pass\n",
            }
            result = _handle_file_mutation("replace_file_content", args, payload)
            self.assertEqual(result.get("decision"), "deny")
            self.assertIn("Fix-The-Code-Not-The-Test Invariant", result.get("reason", ""))
            self.assertIn("dev-be", result.get("reason", ""))

    def test_dev_fe_allowed_to_add_new_assertions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "button.test.tsx")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("test('renders', () => {\n  expect(button).toBeDefined();\n});\n")

            payload = {
                "role": "dev-fe",
                "workspacePaths": [tmpdir],
            }
            # Add new assertion without deleting existing ones
            args = {
                "TargetFile": test_file,
                "Target": "  expect(button).toBeDefined();\n",
                "Replacement": "  expect(button).toBeDefined();\n  expect(button).toHaveTextContent('Click');\n",
            }
            result = _handle_file_mutation("replace_file_content", args, payload)
            reason = result.get("reason", "")
            self.assertNotIn("Fix-The-Code-Not-The-Test Invariant", reason)

    def test_fd_unbounded_extension_blocked_and_bounded_allowed(self) -> None:
        import io, json
        from unittest.mock import patch
        import pre_tool_use_hook

        def run_pre(cmd: str) -> dict:
            input_data = json.dumps({"toolCall": {"name": "run_command", "args": {"CommandLine": cmd}}})
            with patch("sys.stdin", io.StringIO(input_data)):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                    pre_tool_use_hook.main()
                    out = mock_out.getvalue().strip()
                    return json.loads(out) if out else {}

        # fd -e py without bounds is denied
        r1 = run_pre("fd -e py")
        self.assertEqual(r1.get("decision"), "deny")
        self.assertIn("SWE-agent 50-Hit Search Flood Guard", r1.get("reason", ""))

        # fd -e py --max-results 20 with bounds is allowed
        r2 = run_pre("fd -e py --max-results 20")
        self.assertEqual(r2.get("decision"), "allow")

    def test_git_grep_multispace_and_quoted_grep_allowed(self) -> None:
        import io, json
        from unittest.mock import patch
        import pre_tool_use_hook

        def run_pre(cmd: str) -> dict:
            input_data = json.dumps({"toolCall": {"name": "run_command", "args": {"CommandLine": cmd}}})
            with patch("sys.stdin", io.StringIO(input_data)):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                    pre_tool_use_hook.main()
                    out = mock_out.getvalue().strip()
                    return json.loads(out) if out else {}

        # git followed by multiple spaces allowed
        r1 = run_pre("git  grep 'pattern'")
        self.assertEqual(r1.get("decision"), "allow")

        r2 = run_pre("git   grep 'pattern'")
        self.assertEqual(r2.get("decision"), "allow")

        # Escaped quotes with grep allowed
        r3 = run_pre('echo \\"grep\\"')
        self.assertEqual(r3.get("decision"), "allow")

        # Legacy bare grep denied
        r4 = run_pre("grep 'pattern' file.txt")
        self.assertEqual(r4.get("decision"), "deny")
        self.assertIn("Modern CLI Tool Invariant", r4.get("reason", ""))


class TestHookImmunityGuard(unittest.TestCase):
    """Tests that core system hooks are protected against unauthorized modification."""

    def test_unauthorized_roles_blocked_from_hook_mutation(self) -> None:
        hook_path = str(Path.home() / ".gemini" / "config" / "hooks" / "pre_tool_use_hook.py")
        blocked_roles = ["meta-invariant-editor", "meta-domain-editor", "debugger", "dev-fe"]

        for r in blocked_roles:
            payload = {"role": r, "workspacePaths": [str(Path.home())]}
            args = {"TargetFile": hook_path}
            result = _handle_file_mutation("replace_file_content", args, payload)
            self.assertEqual(
                result.get("decision"),
                "deny",
                f"Role '{r}' should be blocked from mutating hooks",
            )
            self.assertIn("Hook Immunity Invariant", result.get("reason", ""))
            self.assertIn(r, result.get("reason", ""))

    def test_dev_be_not_blocked_by_hook_immunity(self) -> None:
        hook_path = str(Path.home() / ".gemini" / "config" / "hooks" / "pre_tool_use_hook.py")
        payload = {"role": "dev-be", "workspacePaths": [str(Path.home())]}
        args = {"TargetFile": hook_path}
        result = _handle_file_mutation("replace_file_content", args, payload)
        reason = result.get("reason", "")
        self.assertNotIn("Hook Immunity Invariant", reason)

    def test_non_hook_path_not_blocked_by_hook_immunity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src_file = os.path.join(tmpdir, "app.py")
            payload = {"role": "meta-invariant-editor", "workspacePaths": [tmpdir]}
            args = {"TargetFile": src_file}
            result = _handle_file_mutation("write_to_file", args, payload)
            reason = result.get("reason", "")
            self.assertNotIn("Hook Immunity Invariant", reason)


class TestValidateHarnessTree(unittest.TestCase):
    """Tests the 4 checks in validate-harness-tree.py."""

    def test_check_always_on_byte_budget(self) -> None:
        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            tf.write("x" * 500)
            tf_path = tf.name
        try:
            ok, msg, count = vht.check_always_on_byte_budget(tf_path, max_chars=1000)
            self.assertTrue(ok)
            self.assertEqual(count, 500)

            ok, msg, count = vht.check_always_on_byte_budget(tf_path, max_chars=400)
            self.assertFalse(ok)
            self.assertIn("Always-On Byte Budget Exceeded", msg)
        finally:
            os.unlink(tf_path)

    def test_check_template_braces_outside_fenced_blocks(self) -> None:
        text = (
            "# Main Heading\n"
            "This has {{ unescaped_variable }} token\n"
            "```python\n"
            "# Inside fence: {{ ignored_variable }} should pass\n"
            "```\n"
            "Escaped \\{{ escaped \\}} should pass\n"
            "Another {% if condition %} token outside\n"
        )
        violations = vht.extract_template_brace_violations(text)
        flagged_lines = [v["line"] for v in violations]
        self.assertIn(2, flagged_lines)
        self.assertNotIn(4, flagged_lines)
        self.assertNotIn(6, flagged_lines)
        self.assertIn(7, flagged_lines)

    def test_skill_coverage_live_harness(self) -> None:
        skills_dir = os.path.expanduser("~/.gemini/antigravity/skills")
        gemini_path = os.path.expanduser("~/.gemini/GEMINI.md")
        pre_inv = os.path.expanduser("~/.gemini/config/hooks/pre_invocation_hook.py")
        skillbank_idx = os.path.expanduser("~/.gemini/antigravity/skillbank/INDEX.md")

        ok, msg, details = vht.check_skill_trigger_coverage(
            skills_dir, gemini_path, pre_inv, skillbank_idx, autotrigger=True
        )
        self.assertTrue(ok, f"All skills should be covered: {msg}")
        self.assertEqual(details["uncovered_count"], 0)
        self.assertEqual(details["total_skills"], 29)

    def test_check_scripts_exist_and_compile(self) -> None:
        hooks_json = os.path.expanduser("~/.gemini/config/hooks.json")
        gemini_md = os.path.expanduser("~/.gemini/GEMINI.md")
        ok, msg, results = vht.check_scripts_exist_and_compile(hooks_json, gemini_md)
        self.assertTrue(ok, f"All hook scripts must exist and compile cleanly: {msg}")
        for r in results:
            self.assertTrue(r["exists"], f"Missing script: {r['path']}")
            self.assertTrue(r["compiles"], f"Compile failure in {r['path']}: {r.get('error')}")

    def test_validate_harness_tree_cli_exit_zero(self) -> None:
        script = _resolve_script_path("validate-harness-tree.py")
        proc = subprocess.run([sys.executable, script, "--json"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Validator failed: {proc.stderr}\n{proc.stdout}")
        data = json.loads(proc.stdout)
        self.assertTrue(data.get("success"), "Validator report success should be True")


class TestCueMatchedMemoryRetrieval(unittest.TestCase):
    """Tests cue matching and SkillBank index retrieval."""

    def test_skillbank_index_structure(self) -> None:
        index_path = Path(os.path.expanduser("~/.gemini/antigravity/skillbank/INDEX.md"))
        self.assertTrue(index_path.is_file(), "SkillBank INDEX.md must exist")
        content = index_path.read_text(encoding="utf-8")
        self.assertIn("# Antigravity SkillBank & Cue Index", content)

        # Check all 28 skills appear in the index
        skills_dir = Path(os.path.expanduser("~/.gemini/antigravity/skills"))
        all_skills = [d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()]
        for s in all_skills:
            self.assertIn(f"`{s}`", content, f"Skill {s} must be indexed in INDEX.md")

    def test_cue_overlap_scoring_logic(self) -> None:
        # Prompt keywords
        prompt_words = {"animation", "physics", "spring", "component"}
        skill_cues = {
            "animation-mastery": ["animation", "spring", "framer-motion", "curves", "motion"],
            "security-audit": ["cve", "auth", "token", "penetration", "vulnerability"],
        }
        scores = {}
        for s_name, cues in skill_cues.items():
            overlap = sum(1 for c in cues if c in prompt_words)
            scores[s_name] = overlap

        self.assertGreater(scores["animation-mastery"], 0)
        self.assertEqual(scores["security-audit"], 0)


class TestRecursivePpcEngine(unittest.TestCase):
    """Tests Level-1 Intra-Task Recursive PPC Engine."""

    def test_script_compiles_and_passes_self_test(self) -> None:
        ppc_script = _resolve_script_path("recursive-ppc-engine.py")
        self.assertTrue(os.path.isfile(ppc_script), f"{ppc_script} must exist")
        py_compile.compile(ppc_script, doraise=True)

        proc = subprocess.run([sys.executable, ppc_script, "--self-test"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Self-test failed: {proc.stderr}\n{proc.stdout}")
        self.assertIn("ALL SELF-TESTS PASSED", proc.stdout)


class TestReflectExperience(unittest.TestCase):
    """Tests Level-2 Inter-Task Experience Reflector and NO_ENTRY confounder gate."""

    def test_script_compiles_and_passes_self_test(self) -> None:
        ref_script = _resolve_script_path("reflect-experience.py")
        self.assertTrue(os.path.isfile(ref_script), f"{ref_script} must exist")
        py_compile.compile(ref_script, doraise=True)

        proc = subprocess.run([sys.executable, ref_script, "--self-test"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Self-test failed: {proc.stderr}\n{proc.stdout}")
        self.assertIn("ALL SELF-TESTS PASSED", proc.stdout)


class TestSotaWaves1To6Upgrades(unittest.TestCase):
    """Covers Waves 1 to 6 SOTA upgrades and Oracle hardening invariants."""

    def test_dev_be_blocked_from_adding_test_skip(self) -> None:
        import pre_tool_use_hook
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_example.py")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("import unittest\nclass T(unittest.TestCase):\n    def test_foo(self): self.assertTrue(True)\n")

            payload = {
                "role": "dev-be",
                "workspacePaths": [tmpdir],
            }
            # Attempt to add skip decorator
            skip_decorator = "@" + "unittest" + ".skip('skip test')\n"
            args = {
                "TargetFile": test_file,
                "TargetContent": "def test_foo(self): self.assertTrue(True)",
                "ReplacementContent": f"{skip_decorator}def test_foo(self): self.assertTrue(True)",
            }
            result = pre_tool_use_hook._handle_file_mutation("replace_file_content", args, payload)
            self.assertEqual(result.get("decision"), "deny")
            self.assertIn("Test-Immutability Lock", result.get("reason", ""))
            self.assertIn(".skip", result.get("reason", ""))

    def test_dev_be_blocked_from_tautological_assertions(self) -> None:
        import pre_tool_use_hook
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_example.py")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("def test_calc():\n    assert calculate(2, 2) == 4\n")

            payload = {
                "role": "dev-be",
                "workspacePaths": [tmpdir],
            }
            # Attempt to replace real assert with tautological assert
            taut_assert = "assert " + "True"
            args = {
                "TargetFile": test_file,
                "TargetContent": "assert calculate(2, 2) == 4",
                "ReplacementContent": taut_assert,
            }
            result = pre_tool_use_hook._handle_file_mutation("replace_file_content", args, payload)
            self.assertEqual(result.get("decision"), "deny")
            self.assertIn("Test-Immutability Lock", result.get("reason", ""))
            self.assertIn("Tautological", result.get("reason", ""))

    def test_ltl_blocks_when_post_edit_command_fails(self) -> None:
        import stop_hook
        with tempfile.TemporaryDirectory() as tmpdir:
            app_file = "/repo/src/app.py"
            tf_path = os.path.join(tmpdir, "transcript.jsonl")
            with open(tf_path, "w", encoding="utf-8") as tf:
                # 0. User input step so this is a top-level session
                tf.write(json.dumps({
                    "type": "USER_INPUT",
                    "content": "Please implement feature"
                }) + "\n")
                # 1. Edit app code
                tf.write(json.dumps({
                    "tool_calls": [{
                        "name": "edit_file",
                        "args": {"Path": app_file, "Target": "x = 1", "Replacement": "x = 2"}
                    }]
                }) + "\n")
                # 2. Run verification command that fails
                tf.write(json.dumps({
                    "tool_calls": [{
                        "name": "run_command",
                        "args": {"CommandLine": "pytest tests/"}
                    }]
                }) + "\n")
                # 3. Output step showing exit code 1
                tf.write(json.dumps({
                    "content": "Command failed with exit code 1\nFAILED (failures=1)"
                }) + "\n")

            payload = {
                "workspacePaths": ["/repo"],
                "transcriptPath": tf_path,
                "conversationId": "test_ltl_fail",
            }
            import io
            from unittest.mock import patch
            with patch("sys.stdin", io.StringIO(json.dumps(payload))):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                    stop_hook.main()
                    out = json.loads(mock_out.getvalue().strip())
                    self.assertEqual(out.get("decision"), "continue")
                    self.assertIn("Anti-Bluffing LTL Gate", out.get("reason", ""))

    def test_post_tool_flags_new_not_implemented_stub(self) -> None:
        import post_tool_use_hook
        stub_code = "raise " + "NotImplementedError('to be done')"
        args = {
            "Replacement": f"def my_func():\n    {stub_code}\n"
        }
        warnings = post_tool_use_hook._check_unfinished_stubs("/repo/src/service.py", args)
        self.assertTrue(len(warnings) > 0)
        self.assertIn("Unfinished Implementation Stub", warnings[0])

    def test_send_message_duplicate_poll_blocked(self) -> None:
        import pre_tool_use_hook
        conv_id = "test_poll_conv"
        ledger_path = os.path.join(tempfile.gettempdir(), f".antigravity_msg_ledger_{conv_id}.json")
        if os.path.exists(ledger_path):
            os.remove(ledger_path)

        payload = {"conversationId": conv_id}
        args1 = {"Recipient": "subagent_123", "Message": "Please report your status"}
        res1 = pre_tool_use_hook._handle_send_message(args1, payload)
        self.assertEqual(res1.get("decision"), "allow")

        res2 = pre_tool_use_hook._handle_send_message(args1, payload)
        self.assertEqual(res2.get("decision"), "deny")
        self.assertIn("Reactive Wakeup Guard", res2.get("reason", ""))

        if os.path.exists(ledger_path):
            os.remove(ledger_path)

    def test_secret_redaction_in_failure_harvester(self) -> None:
        import stop_hook
        leaked = "API token is sk-proj-1234567890abcdef1234567890 and github token is ghp_12345678901234567890123456789012"
        scrubbed = stop_hook._scrub_secrets(leaked)
        self.assertNotIn("sk-proj-1234567890abcdef1234567890", scrubbed)
        self.assertNotIn("ghp_12345678901234567890123456789012", scrubbed)
        self.assertIn("[REDACTED_SECRET]", scrubbed)

    def test_atomic_json_update_flock_safety(self) -> None:
        import pre_tool_use_hook
        with tempfile.NamedTemporaryFile("w", delete=False) as tf:
            tf.write(json.dumps({"count": 0}))
            tf_path = tf.name

        try:
            def increment(data):
                data["count"] += 1
                return data

            res = pre_tool_use_hook._atomic_json_update(tf_path, increment)
            self.assertEqual(res.get("count"), 1)
            updated = pre_tool_use_hook._atomic_json_read(tf_path)
            self.assertEqual(updated.get("count"), 1)
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)
            lock_p = f"{tf_path}.lock"
            if os.path.exists(lock_p):
                os.remove(lock_p)

    def test_mtime_bump_clears_file_slices(self) -> None:
        import pre_tool_use_hook
        test_file = "/repo/test.py"
        test_key = pre_tool_use_hook._normalize(test_file, "")
        ledger = {
            test_key: {
                "file_slices": [(1, 50), (51, 100)],
                "reads_since_edit": 2,
                "whole_reads": 1,
            }
        }
        pre_tool_use_hook._apply_tool_calls_to_ledger([
            {"name": "edit_file", "args": {"Path": test_file}}
        ], ledger, "")
        self.assertEqual(ledger[test_key]["file_slices"], [])
        self.assertEqual(ledger[test_key]["reads_since_edit"], 0)

    def test_proportional_slice_limit_for_2000_line_file(self) -> None:
        import pre_tool_use_hook
        max_slices = pre_tool_use_hook._calculate_max_slices(2000)
        self.assertEqual(max_slices, 10)

        max_slices_large = pre_tool_use_hook._calculate_max_slices(3500)
        self.assertEqual(max_slices_large, 16)

        max_slices_small = pre_tool_use_hook._calculate_max_slices(600)
        self.assertEqual(max_slices_small, 6)

    def test_shell_mutation_blocks_sd_and_python_write(self) -> None:
        import pre_tool_use_hook
        sd_cmd = "sd 'old' 'new' src/main.py"
        target_sd = pre_tool_use_hook._detect_shell_source_mutation(sd_cmd, "/repo")
        self.assertEqual(target_sd, "src/main.py")

        py_cmd = "python3 -c \"open('src/app.py', 'w').write('foo')\""
        target_py = pre_tool_use_hook._detect_shell_source_mutation(py_cmd, "/repo")
        self.assertEqual(target_py, "src/app.py")

    def test_deterministic_kv_cache_sorting(self) -> None:
        import pre_invocation_hook
        allowed = ["z_module.py", "a_module.py", "m_module.py"]
        res = pre_invocation_hook._build_leased_symbols_section(allowed, "")
        self.assertTrue(res.startswith("- Leased File Symbols:\n  - a_module.py:"))

    def test_observation_tombstone_format(self) -> None:
        tool_name = "read_file"
        target = "src/big.ts"
        start_l, end_l = 1, 250
        tokens_masked = 1200
        tombstone = f"[Elided {tool_name}({target}, L{start_l}-L{end_l}) — {tokens_masked} tokens masked]"
        self.assertIn("tokens masked", tombstone)
        self.assertIn("src/big.ts", tombstone)

    def test_error_stagnation_circuit_breaker_blocks_fourth_identical_error(self) -> None:
        import pre_tool_use_hook
        conv_id = "test_err_stag_conv"
        ledger_path = os.path.join(tempfile.gettempdir(), f".antigravity_err_sig_{conv_id}.json")
        try:
            dummy_sig = "dummy_sha256_hash_12345"
            pre_tool_use_hook._atomic_json_write(ledger_path, {
                "signatures": [dummy_sig, dummy_sig, dummy_sig]
            })
            payload = {"conversationId": conv_id}
            res = pre_tool_use_hook._check_error_stagnation_circuit_breaker(payload, "run_command", {"CommandLine": "pytest"})
            self.assertIsNotNone(res)
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("Error-Stagnation Circuit Breaker", res.get("reason", ""))
        finally:
            if os.path.exists(ledger_path):
                os.remove(ledger_path)

    def test_ruff_f821_undefined_name_flagged(self) -> None:
        import post_tool_use_hook
        import shutil
        if not shutil.which("ruff"):
            self.skipTest("ruff not available in environment")
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write("def foo():\n    return undefined_variable_name_xyz\n")
            tf_path = tf.name

        try:
            os.environ["ANTIGRAVITY_ENABLE_RUFF_F821"] = "1"
            err = post_tool_use_hook._check_python_syntax(tf_path)
            self.assertIsNotNone(err)
            self.assertIn("Ruff Diagnostic", err)
            self.assertIn("F821", err)
        finally:
            os.environ.pop("ANTIGRAVITY_ENABLE_RUFF_F821", None)
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_select_affected_tests_cli(self) -> None:
        script = _resolve_script_path("select-affected-tests.py")
        self.assertTrue(os.path.isfile(script), f"{script} must exist")
        proc = subprocess.run([sys.executable, script, "--help"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("select-affected-tests", proc.stdout.lower())

    def test_subagent_scope_drift_detector(self) -> None:
        import stop_hook
        import time
        conv_id = "test_drift_conv"
        with tempfile.TemporaryDirectory() as tmpdir:
            tf_path = os.path.join(tmpdir, "transcript.jsonl")
            with open(tf_path, "w", encoding="utf-8") as tf:
                tf.write(json.dumps({
                    "content": "You are Builder B1. allowed_files: ['src/allowed.py']"
                }) + "\n")

            tracker_path = os.path.join(tempfile.gettempdir(), f".antigravity_superseded_{conv_id}.json")
            try:
                stop_hook.Path(tracker_path).write_text(json.dumps({
                    os.path.join(tmpdir, "src/unleased.py"): {"mutated_at": time.time()}
                }), encoding="utf-8")

                payload = {
                    "conversationId": conv_id,
                    "transcriptPath": tf_path,
                    "workspacePaths": [tmpdir],
                    "agentRole": "dev-be",
                }
                warnings = stop_hook._check_subagent_scope_drift(payload)
                self.assertTrue(len(warnings) > 0)
                self.assertIn("Scope drift detected", warnings[0])
            finally:
                if os.path.exists(tracker_path):
                    os.remove(tracker_path)


class TestSemanticOracleCustodyAndMutationProbe(unittest.TestCase):
    """Tests Semantic Oracle Custody and Diff-Scoped Differential Mutation Probe."""

    def test_semantic_oracle_custody_blocks_literal_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_calculator.py")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("def test_calc():\n    assert calc(10) == 15\n")

            payload = {
                "role": "dev-be",
                "workspacePaths": [tmpdir],
            }
            args = {
                "TargetFile": test_file,
                "TargetContent": "assert calc(10) == 15",
                "ReplacementContent": "assert calc(10) == 0",
            }
            result = _handle_file_mutation("replace_file_content", args, payload)
            self.assertEqual(result.get("decision"), "deny")
            self.assertIn("Semantic Oracle Custody Lock", result.get("reason", ""))
            self.assertIn("Mutating expected assertion literal values", result.get("reason", ""))

    def test_semantic_oracle_custody_blocks_operator_weakening(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_sample.py")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("def test_foo():\n    assert x == 5\n")

            payload = {
                "role": "dev-be",
                "workspacePaths": [tmpdir],
            }
            args = {
                "TargetFile": test_file,
                "TargetContent": "assert x == 5",
                "ReplacementContent": "assert x is not None",
            }
            result = _handle_file_mutation("replace_file_content", args, payload)
            self.assertEqual(result.get("decision"), "deny")
            self.assertIn("Semantic Oracle Custody Lock", result.get("reason", ""))
            self.assertIn("Weakening strict equality assertions", result.get("reason", ""))

    def test_semantic_oracle_custody_allows_update_with_env_lease(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_calc.py")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("def test_calc():\n    assert calc(10) == 15\n")

            payload = {
                "role": "dev-be",
                "workspacePaths": [tmpdir],
            }
            args = {
                "TargetFile": test_file,
                "TargetContent": "assert calc(10) == 15",
                "ReplacementContent": "assert calc(10) == 0",
            }
            try:
                os.environ["ORACLE_CUSTODY_LEASE"] = "1"
                result = _handle_file_mutation("replace_file_content", args, payload)
                self.assertNotEqual(result.get("decision"), "deny")
            finally:
                os.environ.pop("ORACLE_CUSTODY_LEASE", None)

    def test_semantic_oracle_custody_allows_update_with_transcript_lease(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_calc.py")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("def test_calc():\n    assert x == 5\n")

            payload = {
                "role": "dev-be",
                "workspacePaths": [tmpdir],
                "transcript": [{
                    "content": "Oracle-Custody-Lease: UPDATE_ASSERTIONS\nUpdating test assertions authorized."
                }],
            }
            args = {
                "TargetFile": test_file,
                "TargetContent": "assert x == 5",
                "ReplacementContent": "assert x is not None",
            }
            result = _handle_file_mutation("replace_file_content", args, payload)
            self.assertNotEqual(result.get("decision"), "deny")

    def test_semantic_oracle_custody_allows_update_with_plan_lease(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_calc.py")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("def test_calc():\n    assert x == 5\n")

            plan_file = os.path.join(tmpdir, "implementation_plan.md")
            with open(plan_file, "w", encoding="utf-8") as f:
                f.write("# Implementation Plan\nOracle-Custody-Lease: UPDATE_ASSERTIONS\n")

            payload = {
                "role": "dev-be",
                "workspacePaths": [tmpdir],
            }
            args = {
                "TargetFile": test_file,
                "TargetContent": "assert x == 5",
                "ReplacementContent": "assert x is not None",
            }
            result = _handle_file_mutation("replace_file_content", args, payload)
            self.assertNotEqual(result.get("decision"), "deny")

    def test_lease_holder_still_blocked_from_skip_and_zero_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_calc.py")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("def test_calc():\n    assert calc(10) == 15\n")

            payload = {
                "role": "dev-be",
                "workspacePaths": [tmpdir],
            }
            try:
                os.environ["ORACLE_CUSTODY_LEASE"] = "1"
                skip_dec = "@" + "unittest" + ".skip('skip test')\n"
                args = {
                    "TargetFile": test_file,
                    "TargetContent": "def test_calc():\n    assert calc(10) == 15",
                    "ReplacementContent": f"{skip_dec}def test_calc():\n    assert calc(10) == 15",
                }
                res_skip = _handle_file_mutation("replace_file_content", args, payload)
                self.assertEqual(res_skip.get("decision"), "deny")
                self.assertIn("Test-Immutability Lock", res_skip.get("reason", ""))

                exit_call = "sys" + ".exit(0)"
                args_exit = {
                    "TargetFile": test_file,
                    "TargetContent": "assert calc(10) == 15",
                    "ReplacementContent": f"import sys; {exit_call}",
                }
                res_exit = _handle_file_mutation("replace_file_content", args_exit, payload)
                self.assertEqual(res_exit.get("decision"), "deny")
                self.assertIn(exit_call, res_exit.get("reason", ""))
            finally:
                os.environ.pop("ORACLE_CUSTODY_LEASE", None)

    def test_mutation_probe_skips_comments_docstrings_logging(self) -> None:
        qc_path = _resolve_script_path("run-compiled-qc.py")
        qc_spec = importlib.util.spec_from_file_location("run_compiled_qc", qc_path)
        qc = importlib.util.module_from_spec(qc_spec)
        qc_spec.loader.exec_module(qc)

        self.assertTrue(qc._is_equivalent_or_non_semantic_line("    # comment with True"))
        self.assertTrue(qc._is_equivalent_or_non_semantic_line("    // comment with =="))
        self.assertTrue(qc._is_equivalent_or_non_semantic_line("    /* block comment with True */"))
        self.assertTrue(qc._is_equivalent_or_non_semantic_line("    * asterisk comment line"))
        self.assertTrue(qc._is_equivalent_or_non_semantic_line('    """Triple quoted docstring"""'))
        self.assertTrue(qc._is_equivalent_or_non_semantic_line("    '''Single triple quoted docstring'''"))
        self.assertTrue(qc._is_equivalent_or_non_semantic_line("    logger.info('status == True')"))
        self.assertTrue(qc._is_equivalent_or_non_semantic_line("    logging.debug('value <= 10')"))
        self.assertTrue(qc._is_equivalent_or_non_semantic_line("    print('score >= 100')"))
        self.assertTrue(qc._is_equivalent_or_non_semantic_line("    console.log('test == False')"))
        self.assertTrue(qc._is_equivalent_or_non_semantic_line("    if TYPE_CHECKING:"))
        self.assertTrue(qc._is_equivalent_or_non_semantic_line("    if __name__ == '__main__':"))
        self.assertFalse(qc._is_equivalent_or_non_semantic_line("    if x == 5:"))
        self.assertFalse(qc._is_equivalent_or_non_semantic_line("    return True"))

    def test_mutation_probe_detects_survived_mutant(self) -> None:
        qc_path = _resolve_script_path("run-compiled-qc.py")
        qc_spec = importlib.util.spec_from_file_location("run_compiled_qc", qc_path)
        qc = importlib.util.module_from_spec(qc_spec)
        qc_spec.loader.exec_module(qc)

        with tempfile.TemporaryDirectory() as tmpdir:
            src_file = os.path.join(tmpdir, "calc.py")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write("def is_positive(x):\n    if x > 0:\n        return True\n    return False\n")

            test_cmd = f"{sys.executable} -c 'exit(0)'"
            res = qc.run_differential_mutation_probe(src_file, test_cmd, timeout=5.0, max_mutants=2)

            self.assertEqual(res.get("status"), "MUTANT_SURVIVED")
            self.assertFalse(res.get("mutant_killed"))
            self.assertGreater(res.get("mutants_tested", 0), 0)
            self.assertGreater(len(res.get("survived_mutants", [])), 0)

            with open(src_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("return True", content)
            self.assertIn("if x > 0:", content)

    def test_mutation_probe_detects_killed_mutant(self) -> None:
        qc_path = _resolve_script_path("run-compiled-qc.py")
        qc_spec = importlib.util.spec_from_file_location("run_compiled_qc", qc_path)
        qc = importlib.util.module_from_spec(qc_spec)
        qc_spec.loader.exec_module(qc)

        with tempfile.TemporaryDirectory() as tmpdir:
            src_file = os.path.join(tmpdir, "calc.py")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write("def is_positive(x):\n    return True\n")

            test_cmd = f"{sys.executable} -c 'from calc import is_positive; assert is_positive(1) is True'"
            res = qc.run_differential_mutation_probe(
                src_file,
                f"PYTHONPATH={tmpdir} {test_cmd}",
                timeout=5.0,
                max_mutants=1,
            )
            self.assertEqual(res.get("status"), "MUTANT_KILLED")
            self.assertTrue(res.get("mutant_killed"))
            self.assertEqual(len(res.get("survived_mutants", [])), 0)
            self.assertEqual(res.get("mutants_tested"), 1)


class TestCodeModeMcpGuidanceAndExtraction(unittest.TestCase):
    """Verifies that Outline-First Monolithic Guard and Slice Loop Breaker suggest extract_symbols and batch_query."""

    def _run_hook(self, payload: dict) -> dict:
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                pre_tool_use_hook.main()
                output = mock_out.getvalue().strip()
                return json.loads(output) if output else {}

    def test_monolithic_outline_guard_suggests_extract_symbols_and_batch_query(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            for i in range(500):
                f.write(f"def func_{i}(): pass\n")
            big_file = f.name
        try:
            payload = {
                "toolCall": {
                    "name": "view_file",
                    "args": {"AbsolutePath": big_file},
                }
            }
            res = self._run_hook(payload)
            self.assertEqual(res.get("decision"), "deny")
            reason = res.get("reason", "")
            self.assertIn("Outline-First Monolithic File Guard", reason)
            self.assertIn("codegraph:extract_symbols(root, path, symbols)", reason)
            self.assertIn("codegraph:batch_query", reason)
        finally:
            if os.path.isfile(big_file):
                os.remove(big_file)

    def test_slice_loop_breaker_suggests_extract_symbols_and_batch_query(self) -> None:
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
                                "EndLine": (idx + 1) * 50,
                            }
                        }]
                    }) + "\n")
                tf_path = tf.name

            try:
                res = self._run_hook({
                    "transcriptPath": tf_path,
                    "toolCall": {
                        "name": "view_file",
                        "args": {
                            "AbsolutePath": large_file,
                            "StartLine": 301,
                            "EndLine": 350,
                        }
                    }
                })
                self.assertEqual(res.get("decision"), "deny")
                reason = res.get("reason", "")
                self.assertIn("Slice Loop Breaker ACTIVATED", reason)
                self.assertIn("codegraph:extract_symbols(root, path, symbols)", reason)
                self.assertIn("codegraph:batch_query", reason)
            finally:
                if os.path.isfile(tf_path):
                    os.remove(tf_path)
        finally:
            if os.path.isfile(large_file):
                os.remove(large_file)


if __name__ == "__main__":
    unittest.main()
