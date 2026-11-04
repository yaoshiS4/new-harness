#!/usr/bin/env python3
"""Harmonization unit tests covering verification command detection,

behavioral anti-pattern grounding, and task-harness graduation.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
import unittest

HOOKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

SCRIPTS_DIR = os.path.abspath(os.path.join(HOOKS_DIR, "..", "..", "antigravity", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import stop_hook
from pre_invocation_hook import (
    _build_session_start_anchor,
    _build_turn1_grounding,
    _compose_static_prefix_pin,
    _get_active_behavioral_antipatterns,
)

ppc_engine_path = os.path.join(SCRIPTS_DIR, "recursive-ppc-engine.py")
ppc_spec = importlib.util.spec_from_file_location("recursive_ppc_engine", ppc_engine_path)
ppc = importlib.util.module_from_spec(ppc_spec)
ppc_spec.loader.exec_module(ppc)


class TestVerificationCommandDetection(unittest.TestCase):
    """Verifies deterministic detection of verification commands in stop_hook."""

    def test_missing_and_empty_arguments_backward_compat(self) -> None:
        self.assertTrue(stop_hook._is_verification_command({}))
        self.assertTrue(stop_hook._is_verification_command({"CommandLine": ""}))
        self.assertTrue(stop_hook._is_verification_command({"command": "   "}))

    def test_trivial_non_verification_commands_rejected(self) -> None:
        trivial_cmds = [
            "echo 'done'",
            "ls -la",
            "eza -l",
            "pwd",
            "cat README.md",
            "head -n 20 main.py",
            "tail -f log.txt",
            "rg 'pattern' src/",
            "fd 'search' .",
            "true",
            "git status",
            "git diff HEAD~1",
            "git log -n 5",
            "git show HEAD",
            "git branch -a",
        ]
        for cmd in trivial_cmds:
            with self.subTest(cmd=cmd):
                self.assertFalse(
                    stop_hook._is_verification_command({"CommandLine": cmd}),
                    f"Command {cmd!r} should NOT be recognized as a verification command",
                )

    def test_trivial_echo_with_keyword_rejected(self) -> None:
        self.assertFalse(
            stop_hook._is_verification_command({"CommandLine": "echo 'pytest tests/'"}),
        )
        self.assertFalse(
            stop_hook._is_verification_command({"CommandLine": 'echo "cargo test" && git status'}),
        )

    def test_verification_patterns_recognized(self) -> None:
        valid_verif_cmds = [
            "pytest",
            "py.test tests/",
            "python3 -m unittest discover -s tests -p 'test_*.py'",
            "vitest run",
            "jest --coverage",
            "mocha tests/**/*.js",
            "cypress run",
            "playwright test",
            "npm test",
            "npm run test",
            "npm run check",
            "npm run lint",
            "npm run build",
            "npm run typecheck",
            "pnpm test",
            "pnpm run lint",
            "yarn test",
            "bun test",
            "cargo test --all",
            "cargo check",
            "cargo clippy",
            "cargo audit",
            "tsc --noEmit",
            "ruff check .",
            "flake8 .",
            "mypy src/",
            "pyright .",
            "python3 -m py_compile app.py",
            "node -c server.js",
            "./scripts/verify-oracle.sh",
            "./test-3-round-loop.sh",
            "run-compiled-qc.sh",
            "python3 validate-harness-tree.py",
            "go test ./...",
            "go vet ./...",
            "gradle test",
            "mvn test",
            "ctest --verbose",
            "make test",
            "make check",
            "bash -n setup.sh",
            "sh -n entry.sh",
            "zsh -n hook.zsh",
            "python3 -m json.tool config.json",
            "madge --circular src/",
            "pip-audit",
            "npm audit",
            "python3 test_auth.py",
            "python3 server.test.ts",
            "python3 ui.spec.js",
            "python3 recursive-ppc-engine.py --self-test",
        ]
        for cmd in valid_verif_cmds:
            with self.subTest(cmd=cmd):
                self.assertTrue(
                    stop_hook._is_verification_command({"CommandLine": cmd}),
                    f"Command {cmd!r} should be recognized as a verification command",
                )

    def test_chained_verification_commands(self) -> None:
        self.assertTrue(
            stop_hook._is_verification_command({"CommandLine": "git status && pytest tests/"})
        )
        self.assertTrue(
            stop_hook._is_verification_command({"CommandLine": "cd /tmp; cargo test"})
        )
        self.assertTrue(
            stop_hook._is_verification_command({"CommandLine": "echo 'start' && tsc --noEmit"})
        )
        self.assertFalse(
            stop_hook._is_verification_command({"CommandLine": "echo 'hello' && git status"})
        )

    def test_file_manipulation_vs_execution_verification_distinction(self) -> None:
        """Verify non-runner commands with test files are rejected, while test execution commands pass."""
        non_verif_cmds = [
            "git checkout tests/test_foo.py",
            "git add tests/test_foo.py",
            "rm tests/test_foo.py",
            "bat tests/test_foo.py",
            "touch tests/test_foo.py",
        ]
        for cmd in non_verif_cmds:
            with self.subTest(cmd=cmd):
                self.assertFalse(
                    stop_hook._is_verification_command({"CommandLine": cmd}),
                    f"Command {cmd!r} should NOT be recognized as a verification command",
                )

        verif_cmds = [
            "python3 tests/test_foo.py",
            "./tests/test_foo.py",
        ]
        for cmd in verif_cmds:
            with self.subTest(cmd=cmd):
                self.assertTrue(
                    stop_hook._is_verification_command({"CommandLine": cmd}),
                    f"Command {cmd!r} should be recognized as a verification command",
                )

    def _run_stop(self, payload: dict) -> dict:
        from unittest.mock import patch
        input_data = json.dumps(payload)
        with patch("sys.stdin", io.StringIO(input_data)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                stop_hook.main()
                val = mock_out.getvalue().strip()
                return json.loads(val) if val else {}

    def test_stop_hook_transcript_spoofing_prevented(self) -> None:
        conv_id = f"test_ltl_spoof_{int(os.getpid())}"
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
                    "args": {"CommandLine": "git status"}
                }]
            }) + "\n")
            tf_path = tf.name

        flag_p = Path(tempfile.gettempdir()) / f"antigravity_verify_alert_{conv_id}.flag"
        try:
            if flag_p.is_file():
                flag_p.unlink()
            payload = {
                "terminationReason": "model_stop",
                "conversationId": conv_id,
                "transcriptPath": tf_path,
                "workspace": "/workspace",
            }
            gate_res = self._run_stop(payload)
            self.assertEqual(gate_res.get("decision"), "continue")
            self.assertIn("Verification Gate Alert", gate_res.get("reason", ""))

            # Now append a genuine verification command (pytest)
            if flag_p.is_file():
                flag_p.unlink()
            with open(tf_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "tool_calls": [{
                        "name": "run_command",
                        "args": {"CommandLine": "pytest tests/test_feature.py"}
                    }]
                }) + "\n")

            gate_res_after = self._run_stop(payload)
            self.assertEqual(gate_res_after.get("decision"), "allow")
        finally:
            if os.path.isfile(tf_path):
                os.remove(tf_path)
            if flag_p.is_file():
                flag_p.unlink()


class TestBehavioralAntiPatternGrounding(unittest.TestCase):
    """Verifies Turn-1 structured feedback and behavioral anti-pattern injection."""

    def test_empty_when_no_feedback_and_no_db(self) -> None:
        res = _get_active_behavioral_antipatterns(conv_id="nonexistent_conv_123")
        self.assertIsInstance(res, list)

    def test_structured_feedback_file_extraction(self) -> None:
        conv_id = f"test_conv_feedback_{int(os.getpid())}"
        diag_file = os.path.join(tempfile.gettempdir(), f".antigravity_structured_feedback_{conv_id}.json")
        try:
            with open(diag_file, "w", encoding="utf-8") as f:
                json.dump({
                    "failure_label": "SyntaxError",
                    "file": "server.py",
                    "line": 42,
                    "message": "unexpected EOF while parsing",
                }, f)

            antipatterns = _get_active_behavioral_antipatterns(conv_id=conv_id)
            self.assertTrue(len(antipatterns) >= 1)
            first = antipatterns[0]
            self.assertIn("Recent Tool Failure", first)
            self.assertIn("SyntaxError at server.py:42", first)
            self.assertIn("unexpected EOF while parsing", first)
        finally:
            if os.path.exists(diag_file):
                os.remove(diag_file)

    def test_registry_sqlite_query_unresolved_failures(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_p = os.path.join(td, "registry.sqlite")
            conn = sqlite3.connect(db_p)
            conn.execute("""
                CREATE TABLE harness_failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id TEXT,
                    failure_type TEXT,
                    reason TEXT,
                    resolved_at DATETIME
                );
            """)
            conn.execute("""
                INSERT INTO harness_failures (conv_id, failure_type, reason, resolved_at)
                VALUES ('c1', 'jev_loop', 'Jev 3-strike repeated edits', NULL);
            """)
            conn.execute("""
                INSERT INTO harness_failures (conv_id, failure_type, reason, resolved_at)
                VALUES ('c2', 'jev_loop', 'Jev 3-strike repeated edits', NULL);
            """)
            conn.execute("""
                INSERT INTO harness_failures (conv_id, failure_type, reason, resolved_at)
                VALUES ('c3', 'pre_tool_deny', 'Destructive command blocked', NULL);
            """)
            conn.commit()
            conn.close()

            antipatterns = _get_active_behavioral_antipatterns(conv_id="c_other", registry_db_path=db_p)
            self.assertTrue(len(antipatterns) >= 1)
            self.assertTrue(any("jev_loop (count=2)" in a for a in antipatterns))

    def test_turn1_grounding_injection_with_antipatterns(self) -> None:
        conv_id = f"test_conv_turn1_{int(os.getpid())}"
        diag_file = os.path.join(tempfile.gettempdir(), f".antigravity_structured_feedback_{conv_id}.json")
        try:
            with open(diag_file, "w", encoding="utf-8") as f:
                json.dump({
                    "failure_label": "UnboundLocalError",
                    "file": "calc.py",
                    "line": 15,
                    "message": "local variable referenced before assignment",
                }, f)

            with tempfile.TemporaryDirectory() as td:
                payload = {
                    "conversationId": conv_id,
                    "prompt": "Fix bug in calc",
                    "workspace": td,
                }
                grounding = _build_turn1_grounding("test_slug", td, payload)
                self.assertIn("Active Knowledge Grounding", grounding)
                self.assertIn("Behavioral Anti-Patterns:", grounding)
                self.assertIn("UnboundLocalError at calc.py:15", grounding)
        finally:
            if os.path.exists(diag_file):
                os.remove(diag_file)

    def test_structured_feedback_stale_and_consumption(self) -> None:
        """Verify stale feedback (>180s) is ignored & unlinked, and fresh feedback is consumed when consume_feedback=True."""
        # 1. Stale feedback (>180s)
        conv_id_stale = f"test_stale_{int(os.getpid())}"
        diag_file_stale = os.path.join(tempfile.gettempdir(), f".antigravity_structured_feedback_{conv_id_stale}.json")
        try:
            with open(diag_file_stale, "w", encoding="utf-8") as f:
                json.dump({
                    "failure_label": "OldError",
                    "timestamp": time.time() - 300,
                    "file": "old.py",
                    "line": 1,
                    "message": "stale failure",
                }, f)
            self.assertTrue(os.path.exists(diag_file_stale))
            antipatterns = _get_active_behavioral_antipatterns(conv_id=conv_id_stale, registry_db_path="/nonexistent")
            self.assertFalse(any("OldError" in a for a in antipatterns), "Stale feedback must be ignored")
            self.assertFalse(os.path.exists(diag_file_stale), "Stale feedback file must be unlinked")
        finally:
            if os.path.exists(diag_file_stale):
                os.remove(diag_file_stale)

        # 2. Fresh feedback consumed after 1 read when consume_feedback=True
        conv_id_fresh = f"test_fresh_{int(os.getpid())}"
        diag_file_fresh = os.path.join(tempfile.gettempdir(), f".antigravity_structured_feedback_{conv_id_fresh}.json")
        try:
            with open(diag_file_fresh, "w", encoding="utf-8") as f:
                json.dump({
                    "failure_label": "FreshError",
                    "timestamp": time.time(),
                    "file": "fresh.py",
                    "line": 10,
                    "message": "fresh failure",
                }, f)
            self.assertTrue(os.path.exists(diag_file_fresh))
            antipatterns = _get_active_behavioral_antipatterns(
                conv_id=conv_id_fresh, registry_db_path="/nonexistent", consume_feedback=True
            )
            self.assertTrue(any("FreshError" in a for a in antipatterns), "Fresh feedback must be extracted")
            self.assertFalse(os.path.exists(diag_file_fresh), "Fresh feedback file must be unlinked after consumption")

            # Second read should now find nothing since it was consumed
            antipatterns_second = _get_active_behavioral_antipatterns(
                conv_id=conv_id_fresh, registry_db_path="/nonexistent"
            )
            self.assertFalse(any("FreshError" in a for a in antipatterns_second), "Consumed feedback must not appear again")
        finally:
            if os.path.exists(diag_file_fresh):
                os.remove(diag_file_fresh)


class TestTaskHarnessGraduationPipeline(unittest.TestCase):
    """Verifies candidate overlay validation and promotion into global settings_reviews."""

    def test_missing_overlay_returns_keep_base(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            res = ppc.promote_validated_candidates(workspace=td)
            self.assertFalse(res["promoted"])
            self.assertEqual(res["decision"], "KEEP_BASE")

    def test_compilation_failure_blocks_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "workspace"
            ws.mkdir()
            ppc.mount_task_harness(ws)
            overlay = ws / ".antigravity" / "task_harness"
            verify_py = overlay / "scripts" / "verify_task.py"
            state_file = overlay / "state.json"
            reg_db = os.path.join(td, "registry.sqlite")

            state_file.write_text(json.dumps({"last_delta": 4.0}), encoding="utf-8")
            verify_py.write_text("def broken_syntax(:\n    pass\n", encoding="utf-8")

            res = ppc.promote_validated_candidates(workspace=str(ws), registry_db_path=reg_db)
            self.assertFalse(res["promoted"])
            self.assertEqual(res["decision"], "KEEP_BASE")
            self.assertIn("py_compile_failure", res["reason"])

    def test_non_positive_delta_blocks_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "workspace"
            ws.mkdir()
            ppc.mount_task_harness(ws)
            overlay = ws / ".antigravity" / "task_harness"
            state_file = overlay / "state.json"
            reg_db = os.path.join(td, "registry.sqlite")

            state_file.write_text(json.dumps({"last_delta": -1.0}), encoding="utf-8")

            res = ppc.promote_validated_candidates(workspace=str(ws), registry_db_path=reg_db)
            self.assertFalse(res["promoted"])
            self.assertEqual(res["decision"], "KEEP_BASE")
            self.assertIn("delta non-positive", res["reason"])

    def test_positive_delta_promotes_into_settings_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "my_project"
            ws.mkdir()
            ppc.mount_task_harness(ws)
            overlay = ws / ".antigravity" / "task_harness"
            state_file = overlay / "state.json"
            reg_db = os.path.join(td, "registry.sqlite")

            state_file.write_text(json.dumps({"last_delta": 2.5}), encoding="utf-8")

            res = ppc.promote_validated_candidates(workspace=str(ws), registry_db_path=reg_db)
            self.assertTrue(res["promoted"])
            self.assertEqual(res["decision"], "PROMOTED")
            self.assertIsNotNone(res["review_id"])
            self.assertIn("SKILL.md", res["graduated_files"])

            conn = sqlite3.connect(reg_db)
            cur = conn.cursor()
            row = cur.execute(
                "SELECT slug, reason, event_count FROM settings_reviews WHERE id = ?;",
                (res["review_id"],),
            ).fetchone()
            conn.close()

            self.assertIsNotNone(row)
            self.assertEqual(row[0], "my_project")
            self.assertIn("delta=2.50", row[1])
            self.assertGreaterEqual(row[2], 1)

            updated_state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertTrue(updated_state.get("graduated"))
            self.assertEqual(updated_state.get("graduated_review_id"), res["review_id"])

    def test_cli_promote_candidates_flag(self) -> None:
        import subprocess
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "cli_proj"
            ws.mkdir()
            ppc.mount_task_harness(ws)
            overlay = ws / ".antigravity" / "task_harness"
            state_file = overlay / "state.json"
            reg_db = os.path.join(td, "registry.sqlite")

            state_file.write_text(json.dumps({"last_delta": 4.2}), encoding="utf-8")

            res = subprocess.run([
                sys.executable,
                ppc_engine_path,
                "--workspace", str(ws),
                "--registry-db", reg_db,
                "--promote-candidates",
            ], capture_output=True, text=True)

            self.assertEqual(res.returncode, 0, f"CLI stderr: {res.stderr}")
            data = json.loads(res.stdout)
            self.assertTrue(data.get("promoted"))
            self.assertEqual(data.get("decision"), "PROMOTED")
            self.assertEqual(data.get("delta"), 4.2)
            self.assertIsNotNone(data.get("review_id"))


class TestTuiTableFormatter(unittest.TestCase):
    """Verifies Terminal TUI table formatting, NFC measurement, and column symmetry."""

    def setUp(self) -> None:
        table_script_path = os.path.join(SCRIPTS_DIR, "format-tui-table.py")
        spec = importlib.util.spec_from_file_location("format_tui_table", table_script_path)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)
        self.script_path = table_script_path

    def test_display_width_vietnamese_and_cjk(self) -> None:
        self.assertEqual(self.mod.string_display_width("Ất Mộc"), 6)
        self.assertEqual(self.mod.string_display_width("Tử Vi"), 5)
        self.assertEqual(self.mod.string_display_width("Hello"), 5)
        self.assertEqual(self.mod.string_display_width("你好"), 4)

    def test_strip_markdown_links(self) -> None:
        self.assertEqual(
            self.mod.strip_markdown_links("Nhật chủ [Ất Mộc](file:///apps/bazi.ts)"),
            "Nhật chủ Ất Mộc",
        )
        self.assertEqual(
            self.mod.strip_markdown_links("[Link 1](http://a.com) and [Link 2](https://b.com)"),
            "Link 1 and Link 2",
        )

    def test_wrapping_and_column_symmetry(self) -> None:
        raw_table = (
            "| Mục | Chi tiết |\n"
            "| :--- | :--- |\n"
            "| 1. Bát Tự | Nhật chủ [Ất Mộc](file:///app.ts) đại diện cho bản mệnh âm mộc linh hoạt |\n"
            "| 2. Tử Vi | Cung Mệnh chuyển dịch theo tiểu hạn hàng năm |\n"
        )
        res = self.mod.format_markdown_or_json(raw_table, max_col_width=24)
        lines = res.splitlines()

        total_width = self.mod.string_display_width(lines[0])
        for idx, line in enumerate(lines):
            self.assertEqual(
                self.mod.string_display_width(line),
                total_width,
                f"Line {idx} width mismatch: {line}",
            )

        content_lines = [l for l in lines if l.startswith("│")]
        first_divs = [i for i, ch in enumerate(content_lines[0]) if ch == "│"]
        for idx, cl in enumerate(content_lines[1:], start=1):
            divs = [i for i, ch in enumerate(cl) if ch == "│"]
            self.assertEqual(divs, first_divs, f"Column divider index shift at line {idx}")

    def test_self_test_execution(self) -> None:
        self.assertTrue(self.mod.self_test())


class TestStaticPrefixPinning(unittest.TestCase):
    """Verifies deterministic 8-hex SHA-256 Prefix-Pin and static header placement."""

    def test_deterministic_prefix_pin_and_order_invariance(self) -> None:
        pin1, header1 = _compose_static_prefix_pin(
            slug="antigravity_settings",
            role="root",
            sot_docs=["README.md", "AGENTS.md"],
        )
        pin2, header2 = _compose_static_prefix_pin(
            slug="antigravity_settings",
            role="root",
            sot_docs=["AGENTS.md", "README.md"],
        )
        self.assertEqual(pin1, pin2)
        self.assertEqual(len(pin1), 8)
        self.assertEqual(header1, header2)
        self.assertIn(f"Prefix-Pin: {pin1}", header1)

        pin_diff_role, _ = _compose_static_prefix_pin(
            slug="antigravity_settings",
            role="dev-be",
            sot_docs=["AGENTS.md", "README.md"],
        )
        self.assertNotEqual(pin1, pin_diff_role)

    def test_session_start_anchor_places_prefix_pin_before_volatile_telemetry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            Path(td, "AGENTS.md").write_text("# SOT\n", encoding="utf-8")
            anchor = _build_session_start_anchor("demo_proj", td, {"role": "root"})
            self.assertTrue(anchor.startswith("[Session Grounding Anchor] (demo_proj)"))
            pin_idx = anchor.find("Prefix-Pin:")
            mem_idx = anchor.find("- Memory Keys:")
            self.assertGreater(pin_idx, 0)
            self.assertGreater(mem_idx, pin_idx)


if __name__ == "__main__":
    unittest.main()
