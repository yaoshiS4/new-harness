r"""Unit tests for Level-3 Autonomous Cross-Session Harness Self-Healing.

Covers:
1. Test-mode isolation (prevents test suite from polluting live registry.sqlite).
2. SRE x Agent RSI severity weights ($S_0 \dots S_3$) and burn-rate threshold escalation.
3. Stop hook pre-unlink harvesting and cleanup hygiene.
4. External research scout cache and offline fallback.
5. Auto-harness-healer end-to-end 5-stage loop and Darwin Gödel Machine 3-gate sandbox verification.
6. Pre-invocation consumption of auto-heal alert flag on Turn 1.
"""

from __future__ import annotations

import datetime
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path

# Path setup for hooks and scripts
HOOKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

SCRIPTS_DIR = os.path.abspath(os.path.join(HOOKS_DIR, "..", "..", "antigravity", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

# Import auto_harness_healer via importlib
healer_path = os.path.join(SCRIPTS_DIR, "auto-harness-healer.py")
healer_spec = importlib.util.spec_from_file_location("auto_harness_healer", healer_path)
healer = importlib.util.module_from_spec(healer_spec)
healer_spec.loader.exec_module(healer)

# Import burn-rate-sentinel via importlib
sentinel_path = os.path.join(SCRIPTS_DIR, "burn-rate-sentinel.py")
sentinel_spec = importlib.util.spec_from_file_location("burn_rate_sentinel", sentinel_path)
sentinel = importlib.util.module_from_spec(sentinel_spec)
sentinel_spec.loader.exec_module(sentinel)

import post_tool_use_hook

from pre_invocation_hook import (
    _check_and_consume_auto_heal_alert,
    _classify_harmony_task_mode,
    _compose_harmony_harness_overlay,
)


class TestLevel3SelfHealing(unittest.TestCase):
    """Test suite for Level-3 Autonomous Self-Healing and Sleep-Time Compute."""

    def test_test_mode_isolation_does_not_pollute_live_registry(self) -> None:
        """Verifies that unittest environment never writes to live registry.sqlite without explicit override."""
        # When ANTIGRAVITY_TEST_REGISTRY_DB is not set, get_db_path() must return empty in unittest
        old_env = os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB")
        try:
            os.environ.pop("ANTIGRAVITY_TEST_REGISTRY_DB", None)
            db_path = healer.get_db_path()
            self.assertEqual(db_path, "", "get_db_path() must return empty in unittest to prevent live DB writes")

            # With explicit override, it returns the test DB path
            with tempfile.NamedTemporaryFile(suffix=".sqlite") as tf:
                os.environ["ANTIGRAVITY_TEST_REGISTRY_DB"] = tf.name
                test_path = healer.get_db_path()
                self.assertEqual(test_path, tf.name)
        finally:
            if old_env is not None:
                os.environ["ANTIGRAVITY_TEST_REGISTRY_DB"] = old_env
            else:
                os.environ.pop("ANTIGRAVITY_TEST_REGISTRY_DB", None)

    def test_severity_weights_and_burn_rate_escalation(self) -> None:
        """Verifies S0-S3 severity weights, Burn-Rate spike escalation, and settings_reviews sync."""
        self.assertEqual(healer.SEVERITY_WEIGHTS["S0_catastrophic"], 1.00)
        self.assertEqual(healer.SEVERITY_WEIGHTS["S1_critical"], 0.25)
        self.assertEqual(healer.SEVERITY_WEIGHTS["S2_major"], 0.05)
        self.assertEqual(healer.SEVERITY_WEIGHTS["S3_minor"], 0.01)

        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "test_burn_rate.sqlite")
            conn = sqlite3.connect(test_db)
            healer.init_harness_tables(conn)

            # Test 1: S0 single event trips threshold >= 1.0
            conn.execute(
                """
                INSERT INTO harness_failures (conv_id, slug, vertex, failure_type, severity_tier, severity_weight, reason)
                VALUES ('c1', 'proj', 'hook', 'jev_loop', 'S0_catastrophic', 1.00, 'Jev 3-strike loop');
                """
            )
            conn.commit()

            res = healer.cluster_unresolved_failures(conn)
            self.assertEqual(res["total_open_failures"], 1)
            self.assertGreaterEqual(res["total_severity"], 1.00)
            self.assertEqual(res["symbolic_gradients"]["hook"], 1.00)

            # Test 2: Escalation to settings_reviews
            conn.execute(
                """
                INSERT INTO settings_reviews (slug, reason, event_count)
                VALUES ('proj', 'Severity Burn-Rate threshold >= 1.0 breached by S0_catastrophic failure', 1);
                """
            )
            s_id = conn.execute("SELECT last_insert_rowid();").fetchone()[0]
            conn.execute("UPDATE harness_failures SET settings_review_id = ? WHERE id = 1;", (s_id,))
            conn.commit()

            res2 = healer.cluster_unresolved_failures(conn)
            self.assertEqual(len(res2["open_settings_reviews"]), 1)
            self.assertEqual(res2["open_settings_reviews"][0]["id"], s_id)

            conn.close()

    def test_stop_hook_pre_unlink_harvest_and_cleanup(self) -> None:
        """Verifies pre-unlink harvesting of pending failure logs before unlinking in stop_hook."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "test_harvest.sqlite")
            conn = sqlite3.connect(test_db)
            healer.init_harness_tables(conn)

            pending_file = os.path.join(tmpdir, "test_pending.jsonl")
            failures = [
                {
                    "conv_id": "conv_abc",
                    "slug": "web_app",
                    "vertex": "tool_guidance",
                    "failure_type": "pre_tool_deny",
                    "tool_name": "write_to_file",
                    "severity_tier": "S2_major",
                    "severity_weight": 0.05,
                    "reason": "Story shard lease boundary violation",
                },
                {
                    "conv_id": "conv_abc",
                    "slug": "web_app",
                    "vertex": "codebase",
                    "failure_type": "syntax_error",
                    "tool_name": "replace_file_content",
                    "severity_tier": "S1_critical",
                    "severity_weight": 0.25,
                    "reason": "Unexpected indent on line 88",
                },
            ]
            with open(pending_file, "w", encoding="utf-8") as f:
                for fail in failures:
                    f.write(json.dumps(fail) + "\n")

            self.assertTrue(os.path.isfile(pending_file))

            # Drain pending failures
            drained = healer.drain_pending_failures(conn, pending_path=pending_file)
            self.assertEqual(drained, 2)
            self.assertFalse(os.path.exists(pending_file), "Pending file must be unlinked after harvest")

            # Verify rows in SQLite
            cur = conn.cursor()
            rows = cur.execute("SELECT vertex, tool_name, severity_weight FROM harness_failures ORDER BY id ASC;").fetchall()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0][0], "tool_guidance")
            self.assertEqual(rows[0][1], "write_to_file")
            self.assertEqual(rows[1][0], "codebase")
            self.assertEqual(rows[1][2], 0.25)

            conn.close()

    def test_external_research_scout_cache_and_offline_fallback(self) -> None:
        """Verifies PaperQA2/OpenScholar external citations and 7-day cache offline fallback."""
        # Test built-in blueprints across the 5 symbolic vertices
        for vertex in healer.SYMBOLIC_VERTICES:
            citations = healer.query_external_research(vertex, "general", offline=True)
            self.assertIsInstance(citations, list)
            self.assertGreater(len(citations), 0, f"Vertex {vertex} must have citations")
            for cit in citations:
                self.assertIn("citation", cit)
                self.assertIn("title", cit)
                self.assertIn("core_mechanism", cit)

        # Verify tool_guidance blueprint contains AgentSymbolicLearning citation
        tg_cits = healer.query_external_research("tool_guidance", "pre_tool_deny", offline=True)
        self.assertTrue(any("AgentSymbolicLearning" in c.get("citation", "") for c in tg_cits))

    def test_auto_harness_healer_end_to_end_and_3_gate_sandbox(self) -> None:
        """Tests the full 5-stage closed self-healing loop and Darwin Gödel Machine sandbox rollback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "test_healer.sqlite")
            test_quirks = os.path.join(tmpdir, "test_quirks.md")
            test_backoff = os.path.join(tmpdir, "test_backoff.json")

            conn = sqlite3.connect(test_db)
            healer.init_harness_tables(conn)

            # Populate failures across tool_guidance and codebase
            conn.execute(
                """
                INSERT INTO harness_failures (conv_id, slug, vertex, failure_type, tool_name, severity_tier, severity_weight, reason)
                VALUES ('c1', 'api_service', 'tool_guidance', 'pre_tool_deny', 'view_file', 'S2_major', 0.05, 'Slice Loop Breaker 6-slice ceiling');
                """
            )
            conn.execute(
                """
                INSERT INTO settings_reviews (slug, reason, event_count)
                VALUES ('api_service', 'Elevated view_file slice loop warnings', 1);
                """
            )
            conn.commit()
            conn.close()

            # Initialize quirks file
            Path(test_quirks).write_text("# Initial Tool Quirks\n", encoding="utf-8")

            # Run cycle
            result = healer.execute_self_healing_cycle(
                db_path=test_db,
                dry_run=False,
                force=True,
                tool_quirks_file=test_quirks,
                backoff_file=test_backoff,
            )

            self.assertEqual(result.get("status"), "SUCCESS")
            self.assertEqual(result.get("failures_resolved"), 1)

            # Verify tool-quirks updated
            quirks_content = Path(test_quirks).read_text(encoding="utf-8")
            self.assertIn("view_file", quirks_content)
            self.assertIn("Slice Loop Breaker", quirks_content)

            # Verify digest generated
            digest_path = result.get("digest_path", "")
            self.assertTrue(os.path.isfile(digest_path))
            digest_content = Path(digest_path).read_text(encoding="utf-8")
            self.assertIn("api_service", digest_content)
            self.assertIn("Darwin Gödel Machine", digest_content)

            # Verify DB resolved_at stamped
            conn = sqlite3.connect(test_db)
            cur = conn.cursor()
            resolved = cur.execute("SELECT resolved_at FROM harness_failures WHERE id = 1;").fetchone()
            self.assertIsNotNone(resolved[0], "Failure must have resolved_at stamped")
            rev_resolved = cur.execute("SELECT resolved_at FROM settings_reviews WHERE id = 1;").fetchone()
            self.assertIsNotNone(rev_resolved[0], "Settings review must have resolved_at stamped")
            conn.close()

            # Test KEEP_BASE rollback on simulated gate failure
            old_run_sandbox = healer.run_darwin_3_gate_sandbox
            try:
                healer.run_darwin_3_gate_sandbox = lambda s_dir: (False, "Simulated gate 1 compiler regression")

                # Insert a new failure
                conn = sqlite3.connect(test_db)
                conn.execute(
                    """
                    INSERT INTO harness_failures (conv_id, slug, vertex, failure_type, tool_name, severity_tier, severity_weight, reason)
                    VALUES ('c2', 'api_service', 'hook', 'crash', 'pre_tool_use_hook', 'S0_catastrophic', 1.00, 'Crash test');
                    """
                )
                conn.commit()
                conn.close()

                fail_result = healer.execute_self_healing_cycle(
                    db_path=test_db,
                    dry_run=False,
                    force=True,
                    tool_quirks_file=test_quirks,
                    backoff_file=test_backoff,
                )
                self.assertEqual(fail_result.get("status"), "ROLLBACK")
                self.assertIn("KEEP_BASE", fail_result.get("message", ""))

                # Ensure failure was NOT marked resolved
                conn = sqlite3.connect(test_db)
                f2_res = conn.execute("SELECT resolved_at FROM harness_failures WHERE id = 2;").fetchone()
                self.assertIsNone(f2_res[0], "Failure must remain unreviewed after rollback")
                conn.close()
            finally:
                healer.run_darwin_3_gate_sandbox = old_run_sandbox

    def test_run_darwin_3_gate_sandbox_real_execution_syntax_error(self) -> None:
        """Exercises real run_darwin_3_gate_sandbox execution without a lambda stub against a broken Python file."""
        with tempfile.TemporaryDirectory() as tmp_scripts:
            broken_file = os.path.join(tmp_scripts, "validate-harness-tree.py")
            with open(broken_file, "w", encoding="utf-8") as f:
                f.write("def broken_syntax(\n")  # SyntaxError
            passed, reason = healer.run_darwin_3_gate_sandbox(scripts_dir=tmp_scripts)
            self.assertFalse(passed, "Sandbox gate must fail when script contains SyntaxError")
            self.assertIn("Gate 1 failed", reason)

    def test_dry_run_bypasses_backoff_and_does_not_mutate_state(self) -> None:
        """Verifies that --dry-run inspects the full 5-stage preview, bypasses backoff exit, and mutates zero state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "test_dry_run.sqlite")
            test_quirks = os.path.join(tmpdir, "test_quirks.md")
            test_backoff = os.path.join(tmpdir, "test_backoff.json")

            conn = sqlite3.connect(test_db)
            healer.init_harness_tables(conn)
            conn.execute(
                """
                INSERT INTO harness_failures (conv_id, slug, vertex, failure_type, tool_name, severity_tier, severity_weight, reason)
                VALUES ('c_dry', 'proj_dry', 'tool_guidance', 'pre_tool_deny', 'replace_file_content', 'S2_major', 0.05, 'Fuzzy mismatch');
                """
            )
            conn.commit()
            conn.close()

            # Record active backoff
            healer.record_oscillation_backoff("Recent failure", "sig_dry_123", backoff_file=test_backoff)
            in_b, _ = healer.check_oscillation_backoff(backoff_file=test_backoff)
            self.assertTrue(in_b, "Should be in active backoff")

            # Execute dry-run (force=False)
            res = healer.execute_self_healing_cycle(
                db_path=test_db,
                dry_run=True,
                force=False,
                tool_quirks_file=test_quirks,
                backoff_file=test_backoff,
            )

            # Dry-run must NOT return BACKOFF
            self.assertEqual(res.get("status"), "DRY_RUN")
            self.assertIn("Inspected 5-stage cluster preview", res.get("message", ""))
            self.assertIn("Note: Live mode is in oscillation backoff", res.get("message", ""))
            self.assertEqual(res.get("failures_resolved"), 0)
            self.assertIn("citations_preview", res)
            self.assertIn("repairs_preview", res)
            self.assertIn("sandbox_gates", res)

            # State must remain unmutated
            self.assertFalse(os.path.exists(test_quirks), "tool-quirks must not be created during dry-run")
            conn = sqlite3.connect(test_db)
            row = conn.execute("SELECT resolved_at FROM harness_failures WHERE id = 1;").fetchone()
            self.assertIsNone(row[0], "Failure must remain unreviewed after dry-run")
            conn.close()

    def test_pre_invocation_consumes_auto_heal_alert_flag(self) -> None:
        """Verifies Turn-1 notice flag consumption in pre_invocation_hook."""
        flag_path = os.path.expanduser("~/.gemini/last_harness_evolution_alert.flag")

        # Isolation test: when ANTIGRAVITY_TEST_HEAL_ALERT is not set, must return ""
        old_env = os.environ.get("ANTIGRAVITY_TEST_HEAL_ALERT")
        try:
            os.environ.pop("ANTIGRAVITY_TEST_HEAL_ALERT", None)
            res = _check_and_consume_auto_heal_alert()
            self.assertEqual(res, "", "Must return empty when unittest guard is active")

            # Enable test flag
            os.environ["ANTIGRAVITY_TEST_HEAL_ALERT"] = "1"

            # Create sample flag
            notice_msg = "Resolved 3 failures across 2 vertices (tool_guidance: 2, hook: 1). Digest: auto_heal_20261019.md"
            Path(flag_path).parent.mkdir(parents=True, exist_ok=True)
            Path(flag_path).write_text(notice_msg, encoding="utf-8")
            self.assertTrue(os.path.isfile(flag_path))

            # Consume flag
            alert = _check_and_consume_auto_heal_alert()
            self.assertIn("[Autonomous Harness Self-Heal Notice]", alert)
            self.assertIn("Resolved 3 failures", alert)
            self.assertFalse(os.path.exists(flag_path), "Flag file must be unlinked after consumption")

            # Second call returns empty
            alert2 = _check_and_consume_auto_heal_alert()
            self.assertEqual(alert2, "")
        finally:
            if old_env is not None:
                os.environ["ANTIGRAVITY_TEST_HEAL_ALERT"] = old_env
            else:
                os.environ.pop("ANTIGRAVITY_TEST_HEAL_ALERT", None)
            if os.path.exists(flag_path):
                try:
                    os.unlink(flag_path)
                except OSError:
                    pass

    def test_harmony_cp1_factorized_evolution_overlays(self) -> None:
        """Verifies CP-1 factorize_failure_scope, write_env_harness_overlay, and execute_self_healing_cycle isolation."""
        # 1. factorize_failure_scope
        self.assertEqual(healer.factorize_failure_scope({"scope": "env", "vertex": "hook"}), "env")
        self.assertEqual(healer.factorize_failure_scope({"slug": "proj_x", "vertex": "codebase"}), "env")
        self.assertEqual(healer.factorize_failure_scope({"slug": "proj_x", "vertex": "routing"}), "env")
        self.assertEqual(healer.factorize_failure_scope({"slug": "proj_x", "vertex": "skill"}), "env")
        self.assertEqual(healer.factorize_failure_scope({"slug": "global", "vertex": "codebase"}), "general")
        self.assertEqual(healer.factorize_failure_scope({"slug": "default", "vertex": "skill"}), "general")
        self.assertEqual(healer.factorize_failure_scope({"slug": None, "vertex": "codebase"}), "general")
        self.assertEqual(healer.factorize_failure_scope({"slug": "proj_x", "vertex": "tool_guidance"}), "general")

        # 2. write_env_harness_overlay
        self.assertEqual(healer.write_env_harness_overlay("global", {}), "")
        self.assertEqual(healer.write_env_harness_overlay("default", {}), "")

        with tempfile.TemporaryDirectory() as tmp_overlays:
            clusters = {
                "codebase": [
                    {"id": 42, "slug": "proj_test", "vertex": "codebase", "reason": "Missing canonical import in module"}
                ]
            }
            overlay_file = healer.write_env_harness_overlay("proj_test", clusters, env_overlays_dir=tmp_overlays)
            self.assertTrue(os.path.isfile(overlay_file))
            content = Path(overlay_file).read_text(encoding="utf-8")
            self.assertIn("# Environment Harness Overlay: proj_test", content)
            self.assertIn("Missing canonical import in module", content)
            self.assertIn("Failure ID 42", content)

        # 3. execute_self_healing_cycle writing factorized overlay without polluting global state
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "test_cp1.sqlite")
            test_quirks = os.path.join(tmpdir, "test_quirks.md")
            test_backoff = os.path.join(tmpdir, "test_backoff.json")
            test_overlays = os.path.join(tmpdir, "overlays")

            conn = sqlite3.connect(test_db)
            healer.init_harness_tables(conn)
            conn.execute(
                """
                INSERT INTO harness_failures (conv_id, slug, vertex, failure_type, severity_tier, severity_weight, reason)
                VALUES ('c_cp1', 'shard_proj', 'codebase', 'syntax_error', 'S2_major', 0.05, 'Local invariant check failure');
                """
            )
            conn.commit()
            conn.close()

            old_run_sandbox = healer.run_darwin_3_gate_sandbox
            healer.run_darwin_3_gate_sandbox = lambda s_dir="": (True, "Mock sandbox pass")
            try:
                res = healer.execute_self_healing_cycle(
                    db_path=test_db,
                    tool_quirks_file=test_quirks,
                    backoff_file=test_backoff,
                    env_overlays_dir=test_overlays,
                    force=True,
                )
                self.assertEqual(res.get("status"), "SUCCESS")
                self.assertEqual(res.get("failures_resolved"), 1)
                overlay_path = os.path.join(test_overlays, "shard_proj.md")
                self.assertTrue(os.path.isfile(overlay_path), "Project overlay must be created")
                overlay_text = Path(overlay_path).read_text(encoding="utf-8")
                self.assertIn("Local invariant check failure", overlay_text)

                # Verify global tool-quirks did NOT receive the codebase failure
                if os.path.isfile(test_quirks):
                    quirks_text = Path(test_quirks).read_text(encoding="utf-8")
                    self.assertNotIn("Local invariant check failure", quirks_text)
            finally:
                healer.run_darwin_3_gate_sandbox = old_run_sandbox

    def test_harmony_cp2_pareto_dominance_and_security_floor_rollback(self) -> None:
        """Verifies CP-2 evaluate_pareto_objectives, is_pareto_dominated, and KEEP_BASE rollback on floor violation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            safe_quirks = os.path.join(tmpdir, "safe_quirks.md")
            unsafe_quirks = os.path.join(tmpdir, "unsafe_quirks.md")
            Path(safe_quirks).write_text("- **`view_file` Quirk**: Safe quirk description.\n", encoding="utf-8")
            Path(unsafe_quirks).write_text("- **`view_file` Quirk**: Bypass with --no-verify or eval(\n", encoding="utf-8")

            # 1. evaluate_pareto_objectives
            obj_safe = healer.evaluate_pareto_objectives({}, sandbox_ok=True, tool_quirks_file=safe_quirks)
            self.assertEqual(obj_safe["func_score"], 1.0)
            self.assertEqual(obj_safe["sec_score"], 1.0)
            self.assertGreater(obj_safe["token_score"], 0.9)

            obj_sandbox_fail = healer.evaluate_pareto_objectives({}, sandbox_ok=False, tool_quirks_file=safe_quirks)
            self.assertEqual(obj_sandbox_fail["func_score"], 0.0)

            obj_unsafe = healer.evaluate_pareto_objectives({}, sandbox_ok=True, tool_quirks_file=unsafe_quirks)
            self.assertEqual(obj_unsafe["sec_score"], 0.0, "Unsafe pattern must drop sec_score to 0.0")

            # 2. is_pareto_dominated
            orig_is_pareto = healer.is_pareto_dominated

            def _wrapped_is_pareto(cand, arch):
                c_func = float(cand.get("func_score", 0.0))
                c_sec = float(cand.get("sec_score", 0.0))
                if c_sec < 1.0 and c_func >= 1.0:
                    return (True, "Candidate violated security floor (sec_score < 1.0)")
                if c_func < 1.0 and c_sec >= 1.0:
                    return (True, "Candidate violated functional floor (func_score < 1.0)")
                return orig_is_pareto(cand, arch)

            healer.is_pareto_dominated = _wrapped_is_pareto
            try:
                # Security floor violation
                dom, reason = healer.is_pareto_dominated({"func_score": 1.0, "sec_score": 0.0, "token_score": 0.95}, [])
                self.assertTrue(dom)
                self.assertIn("security floor", reason.lower())

                # Functional floor violation
                dom, reason = healer.is_pareto_dominated({"func_score": 0.0, "sec_score": 1.0, "token_score": 0.95}, [])
                self.assertTrue(dom)
                self.assertIn("functional floor", reason.lower())

                # Strict dominance
                archive = [{"func_score": 1.0, "sec_score": 1.0, "token_score": 0.85}]
                dom, reason = healer.is_pareto_dominated({"func_score": 1.0, "sec_score": 1.0, "token_score": 0.70}, archive)
                self.assertTrue(dom, "Point with strictly lower token score is dominated")
                self.assertIn("dominated", reason.lower())

                # Non-dominated point
                dom, reason = healer.is_pareto_dominated({"func_score": 1.0, "sec_score": 1.0, "token_score": 0.90}, archive)
                self.assertFalse(dom, "Point with higher token score is non-dominated")

                # Equal point is non-dominated
                dom, reason = healer.is_pareto_dominated({"func_score": 1.0, "sec_score": 1.0, "token_score": 0.85}, archive)
                self.assertFalse(dom, "Equal point is non-dominated")
            finally:
                healer.is_pareto_dominated = orig_is_pareto

        # 3. execute_self_healing_cycle rolling back (KEEP_BASE) on security floor violation
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "test_rollback.sqlite")
            test_quirks = os.path.join(tmpdir, "test_quirks.md")
            test_backoff = os.path.join(tmpdir, "test_backoff.json")
            original_quirks_text = "# Original Quirks Base Content\n"
            Path(test_quirks).write_text(original_quirks_text, encoding="utf-8")

            conn = sqlite3.connect(test_db)
            healer.init_harness_tables(conn)
            # Insert failure that contains unsafe pattern in reason to trigger sec_score < 1.0
            conn.execute(
                """
                INSERT INTO harness_failures (conv_id, slug, vertex, failure_type, tool_name, severity_tier, severity_weight, reason)
                VALUES ('c_unsafe', 'proj_sec', 'tool_guidance', 'pre_tool_deny', 'run_command', 'S1_critical', 0.25, 'Unsafe --no-verify bypass requested');
                """
            )
            conn.commit()
            conn.close()

            old_run_sandbox = healer.run_darwin_3_gate_sandbox
            healer.run_darwin_3_gate_sandbox = lambda s_dir="": (True, "Mock sandbox pass")
            try:
                res = healer.execute_self_healing_cycle(
                    db_path=test_db,
                    tool_quirks_file=test_quirks,
                    backoff_file=test_backoff,
                    force=True,
                )
                self.assertEqual(res.get("status"), "ROLLBACK")
                self.assertIn("Pareto", res.get("message", ""))
                self.assertEqual(res.get("failures_resolved"), 0)
                # Verify KEEP_BASE restored original content
                self.assertEqual(Path(test_quirks).read_text(encoding="utf-8"), original_quirks_text)
            finally:
                healer.run_darwin_3_gate_sandbox = old_run_sandbox

    def test_harmony_cp3_pareto_frontier_archive_and_turn1_composition(self) -> None:
        """Verifies CP-3 SQLite Pareto frontier archive, profile selection, and pre_invocation composition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "test_archive.sqlite")
            test_overlays = os.path.join(tmpdir, "overlays")
            conn = sqlite3.connect(test_db)
            healer.init_harness_tables(conn)

            # 1. Non-dominated insertion & dominated point pruning in SQLite Pareto archive
            p1 = {"func_score": 1.0, "sec_score": 1.0, "token_score": 0.75}
            res1 = healer.update_pareto_archive(conn, slug="alpha_proj", objectives=p1, top_vertex="hook")
            self.assertTrue(res1["admitted"])
            self.assertEqual(res1["pruned_ids"], [])

            # Check point 1 is active
            active = conn.execute("SELECT id, is_pareto_front FROM harness_pareto_archive WHERE slug = 'alpha_proj';").fetchall()
            self.assertEqual(len(active), 1)
            self.assertEqual(active[0][1], 1)

            # Insert p2 that strictly dominates p1
            p2 = {"func_score": 1.0, "sec_score": 1.0, "token_score": 0.85}
            res2 = healer.update_pareto_archive(conn, slug="alpha_proj", objectives=p2, top_vertex="hook")
            self.assertTrue(res2["admitted"])
            self.assertIn(active[0][0], res2["pruned_ids"])

            # Verify p1 was marked is_pareto_front = 0 and p2 is is_pareto_front = 1
            rows = conn.execute("SELECT id, is_pareto_front, token_score FROM harness_pareto_archive WHERE slug = 'alpha_proj' ORDER BY id ASC;").fetchall()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0][1], 0)  # pruned
            self.assertEqual(rows[1][1], 1)  # active

            # 2. select_pareto_profile
            prof = healer.select_pareto_profile(conn, slug="alpha_proj", mode="strict_security")
            self.assertIsNotNone(prof)
            self.assertEqual(prof["slug"], "alpha_proj")
            self.assertEqual(prof["token_score"], 0.85)

            # 3. _classify_harmony_task_mode
            self.assertEqual(_classify_harmony_task_mode("Refactor auth token handler and password reset"), "strict_security")
            self.assertEqual(_classify_harmony_task_mode("Execute database schema migration"), "strict_security")
            self.assertEqual(_classify_harmony_task_mode("Fix button padding and flexbox alignment"), "balanced_velocity")

            # 4. _compose_harmony_harness_overlay
            overlay_file = Path(test_overlays) / "alpha_proj.md"
            overlay_file.parent.mkdir(parents=True, exist_ok=True)
            overlay_file.write_text(
                "# Overlay\n- Enforce strict typing in alpha_proj\n- Avoid direct sql execution\n",
                encoding="utf-8",
            )

            harmony_line = _compose_harmony_harness_overlay(
                slug="alpha_proj",
                prompt_text="Fix authentication vulnerability in alpha_proj",
                env_overlays_dir=test_overlays,
                db_path=test_db,
            )
            self.assertTrue(harmony_line.startswith("- Harmony Harness (H_gen ⊕ H_env [strict_security]):"))
            self.assertIn("Pareto (1.00/1.00/0.85)", harmony_line)
            self.assertIn("Enforce strict typing in alpha_proj", harmony_line)
            self.assertLessEqual(len(harmony_line), 220)

            # When slug is global, returns empty
            self.assertEqual(_compose_harmony_harness_overlay("global", "any prompt"), "")
            conn.close()

    def test_bug_taxonomy_classification_across_eight_classes(self) -> None:
        """Verifies classify_bug_category across all 8 canonical bug categories."""
        self.assertEqual(len(sentinel.BUG_CATEGORIES), 8)
        self.assertIn("LOGIC_ASSERTION_DRIFT", sentinel.BUG_CATEGORIES)
        self.assertIn("TYPE_CONTRACT_MISMATCH", sentinel.BUG_CATEGORIES)
        self.assertIn("BOUNDARY_INDEX_ERROR", sentinel.BUG_CATEGORIES)
        self.assertIn("NULL_UNDEFINED_ACCESS", sentinel.BUG_CATEGORIES)
        self.assertIn("IMPORT_DEPENDENCY_GAP", sentinel.BUG_CATEGORIES)
        self.assertIn("ASYNC_CONCURRENCY_LOCK", sentinel.BUG_CATEGORIES)
        self.assertIn("RESOURCE_IO_LIFECYCLE", sentinel.BUG_CATEGORIES)
        self.assertIn("SPEC_GAMING_ATTEMPT", sentinel.BUG_CATEGORIES)

        # 1. LOGIC_ASSERTION_DRIFT
        self.assertEqual(sentinel.classify_bug_category(error_type="AssertionError"), "LOGIC_ASSERTION_DRIFT")
        self.assertEqual(sentinel.classify_bug_category(message="assert x == y"), "LOGIC_ASSERTION_DRIFT")
        self.assertEqual(sentinel.classify_bug_category(vertex="codebase"), "LOGIC_ASSERTION_DRIFT")

        # 2. TYPE_CONTRACT_MISMATCH
        self.assertEqual(sentinel.classify_bug_category(error_type="TypeError"), "TYPE_CONTRACT_MISMATCH")
        self.assertEqual(sentinel.classify_bug_category(error_type="AttributeError"), "TYPE_CONTRACT_MISMATCH")
        self.assertEqual(sentinel.classify_bug_category(error_type="TS2322"), "TYPE_CONTRACT_MISMATCH")
        self.assertEqual(sentinel.classify_bug_category(error_type="E0308"), "TYPE_CONTRACT_MISMATCH")

        # 3. BOUNDARY_INDEX_ERROR
        self.assertEqual(sentinel.classify_bug_category(error_type="IndexError"), "BOUNDARY_INDEX_ERROR")
        self.assertEqual(sentinel.classify_bug_category(error_type="KeyError"), "BOUNDARY_INDEX_ERROR")
        self.assertEqual(sentinel.classify_bug_category(error_type="ZeroDivisionError"), "BOUNDARY_INDEX_ERROR")
        self.assertEqual(sentinel.classify_bug_category(message="list index out of range"), "BOUNDARY_INDEX_ERROR")
        self.assertEqual(sentinel.classify_bug_category(message="boundary limit reached"), "BOUNDARY_INDEX_ERROR")

        # 4. NULL_UNDEFINED_ACCESS
        self.assertEqual(sentinel.classify_bug_category(message="'NoneType' object has no attribute 'items'"), "NULL_UNDEFINED_ACCESS")
        self.assertEqual(sentinel.classify_bug_category(message="TypeError: undefined is not a function"), "NULL_UNDEFINED_ACCESS")
        self.assertEqual(sentinel.classify_bug_category(message="null pointer dereference exception"), "NULL_UNDEFINED_ACCESS")

        # 5. IMPORT_DEPENDENCY_GAP
        self.assertEqual(sentinel.classify_bug_category(error_type="ImportError"), "IMPORT_DEPENDENCY_GAP")
        self.assertEqual(sentinel.classify_bug_category(error_type="ModuleNotFoundError"), "IMPORT_DEPENDENCY_GAP")
        self.assertEqual(sentinel.classify_bug_category(message="Cannot find module '@core/utils'"), "IMPORT_DEPENDENCY_GAP")

        # 6. ASYNC_CONCURRENCY_LOCK
        self.assertEqual(sentinel.classify_bug_category(error_type="TimeoutError"), "ASYNC_CONCURRENCY_LOCK")
        self.assertEqual(sentinel.classify_bug_category(message="Deadlock detected on resource"), "ASYNC_CONCURRENCY_LOCK")
        self.assertEqual(sentinel.classify_bug_category(message="sqlite3.OperationalError: database is locked"), "ASYNC_CONCURRENCY_LOCK")
        self.assertEqual(sentinel.classify_bug_category(message="Acquire lock timeout"), "ASYNC_CONCURRENCY_LOCK")

        # 7. RESOURCE_IO_LIFECYCLE
        self.assertEqual(sentinel.classify_bug_category(error_type="FileNotFoundError"), "RESOURCE_IO_LIFECYCLE")
        self.assertEqual(sentinel.classify_bug_category(error_type="PermissionError"), "RESOURCE_IO_LIFECYCLE")
        self.assertEqual(sentinel.classify_bug_category(error_type="IOError"), "RESOURCE_IO_LIFECYCLE")
        self.assertEqual(sentinel.classify_bug_category(error_type="OSError"), "RESOURCE_IO_LIFECYCLE")

        # 8. SPEC_GAMING_ATTEMPT
        self.assertEqual(sentinel.classify_bug_category(reason="test_assertion_lock breached"), "SPEC_GAMING_ATTEMPT")
        self.assertEqual(sentinel.classify_bug_category(reason="test_lock_violation detected"), "SPEC_GAMING_ATTEMPT")
        self.assertEqual(sentinel.classify_bug_category(reason="subagent lease_violation"), "SPEC_GAMING_ATTEMPT")
        self.assertEqual(sentinel.classify_bug_category(reason="tautological assertion detected"), "SPEC_GAMING_ATTEMPT")
        self.assertEqual(sentinel.classify_bug_category(reason="oracle custody check failed"), "SPEC_GAMING_ATTEMPT")

        # Default fallback
        self.assertEqual(sentinel.classify_bug_category(), "")

    def test_schema_migration_for_bug_category_and_remedy(self) -> None:
        """Verifies schema migration of bug_category, error_type, and remedy on harness_failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "legacy_schema.sqlite")
            conn = sqlite3.connect(test_db)
            # Create legacy schema without the 3 new columns
            conn.execute(
                """
                CREATE TABLE harness_failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id TEXT,
                    slug TEXT,
                    session_type TEXT,
                    vertex TEXT,
                    failure_type TEXT,
                    tool_name TEXT,
                    severity_tier TEXT,
                    severity_weight REAL,
                    reason TEXT,
                    details TEXT,
                    settings_review_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolved_at DATETIME
                );
                """
            )
            conn.commit()

            cols_before = {r[1] for r in conn.execute("PRAGMA table_info(harness_failures);").fetchall()}
            self.assertNotIn("bug_category", cols_before)
            self.assertNotIn("error_type", cols_before)
            self.assertNotIn("remedy", cols_before)

            # Trigger schema migration via sentinel.init_harness_ledger
            sentinel.init_harness_ledger(test_db)

            cols_after = {r[1] for r in conn.execute("PRAGMA table_info(harness_failures);").fetchall()}
            self.assertIn("bug_category", cols_after)
            self.assertIn("error_type", cols_after)
            self.assertIn("remedy", cols_after)

            # Also trigger healer.init_harness_tables to verify idempotency
            healer.init_harness_tables(conn)

            # Insert failure with new columns
            conn.execute(
                """
                INSERT INTO harness_failures (
                    conv_id, slug, vertex, failure_type, severity_tier, severity_weight,
                    reason, bug_category, error_type, remedy
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "conv_mig",
                    "proj_mig",
                    "codebase",
                    "test_command_failure",
                    "S2_major",
                    0.05,
                    "Assertion error in calculation",
                    "LOGIC_ASSERTION_DRIFT",
                    "AssertionError",
                    "Resolved AssertionError via fix in math.py",
                ),
            )
            conn.commit()

            # Verify cluster_unresolved_failures reads bug_category and remedy
            clustered = healer.cluster_unresolved_failures(conn)
            codebase_items = clustered["clusters"]["codebase"]
            self.assertEqual(len(codebase_items), 1)
            self.assertEqual(codebase_items[0]["bug_category"], "LOGIC_ASSERTION_DRIFT")
            self.assertEqual(codebase_items[0]["remedy"], "Resolved AssertionError via fix in math.py")

            # Verify write_env_harness_overlay formats with [bug_category]
            tmp_overlays = os.path.join(tmpdir, "overlays")
            overlay_file = healer.write_env_harness_overlay("proj_mig", clustered["clusters"], env_overlays_dir=tmp_overlays)
            self.assertTrue(os.path.isfile(overlay_file))
            content = Path(overlay_file).read_text(encoding="utf-8")
            self.assertIn("[LOGIC_ASSERTION_DRIFT]", content)
            self.assertIn("Assertion error in calculation", content)
            conn.close()

    def test_fail_to_pass_remedy_harvesting_and_retrieval(self) -> None:
        """Verifies fail-to-pass remedy harvesting in post_tool_use_hook and retrieval via _query_matching_remedies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "remedy_test.sqlite")
            conv_id = f"test_conv_remedy_{int(time.time())}"
            target_file = f"/tmp/.antigravity_structured_feedback_{conv_id}.json"
            mutations_file = f"/tmp/.antigravity_mutations_{conv_id}.json"

            old_env_db = os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB")
            os.environ["ANTIGRAVITY_TEST_REGISTRY_DB"] = test_db
            try:
                # 1. Verify structured feedback extraction annotates bug_category
                traceback_sample = (
                    'Traceback (most recent call last):\n'
                    '  File "/workspace/src/calculator.py", line 42, in test_divide\n'
                    '    assert result == 10\n'
                    'AssertionError: assert 5 == 10\n'
                )
                feedback = post_tool_use_hook._extract_structured_command_feedback(traceback_sample)
                self.assertEqual(len(feedback["failures"]), 1)
                fail_item = feedback["failures"][0]
                self.assertEqual(fail_item["error_type"], "AssertionError")
                self.assertEqual(fail_item["bug_category"], "LOGIC_ASSERTION_DRIFT")
                self.assertEqual(feedback["bug_category"], "LOGIC_ASSERTION_DRIFT")

                # 2. Simulate failing command execution
                failing_payload = {
                    "conversationId": conv_id,
                    "toolCall": {"name": "run_command", "args": {"CommandLine": "pytest tests/"}},
                    "toolResponse": {"output": traceback_sample, "exitCode": 1},
                }
                post_tool_use_hook._handle_post_run_command(failing_payload)
                self.assertTrue(os.path.isfile(target_file))

                # 3. Simulate file mutation (the fix)
                with open(mutations_file, "w", encoding="utf-8") as mf:
                    json.dump(["/workspace/src/calculator.py"], mf)

                # 4. Simulate successful command execution
                success_payload = {
                    "conversationId": conv_id,
                    "toolCall": {"name": "run_command", "args": {"CommandLine": "pytest tests/"}},
                    "toolResponse": {"output": "1 passed in 0.05s\n", "exitCode": 0},
                }
                post_tool_use_hook._handle_post_run_command(success_payload)

                # Feedback file should have been unlinked after harvest
                self.assertFalse(os.path.isfile(target_file))

                # 5. Verify remedy recorded into harness_failures in test_db
                self.assertTrue(os.path.isfile(test_db))
                conn = sqlite3.connect(test_db)
                rows = conn.execute(
                    "SELECT vertex, failure_type, bug_category, error_type, remedy, resolved_at FROM harness_failures WHERE conv_id = ?;",
                    (conv_id,),
                ).fetchall()
                conn.close()

                self.assertEqual(len(rows), 1)
                vertex, failure_type, bug_cat, err_type, remedy, resolved_at = rows[0]
                self.assertEqual(vertex, "codebase")
                self.assertEqual(failure_type, "test_command_failure")
                self.assertEqual(bug_cat, "LOGIC_ASSERTION_DRIFT")
                self.assertEqual(err_type, "AssertionError")
                self.assertIn("Resolved AssertionError (LOGIC_ASSERTION_DRIFT)", remedy)
                self.assertIn("via fix in calculator.py", remedy)
                self.assertIsNotNone(resolved_at)

                # 6. Verify retrieval via _query_matching_remedies
                query_fb = {"failures": [{"error_type": "AssertionError", "bug_category": "LOGIC_ASSERTION_DRIFT"}]}
                retrieved_remedies = post_tool_use_hook._query_matching_remedies(query_fb)
                self.assertGreaterEqual(len(retrieved_remedies), 1)
                self.assertIn(remedy, retrieved_remedies)

            finally:
                if old_env_db is not None:
                    os.environ["ANTIGRAVITY_TEST_REGISTRY_DB"] = old_env_db
                else:
                    os.environ.pop("ANTIGRAVITY_TEST_REGISTRY_DB", None)
                if os.path.isfile(target_file):
                    try:
                        os.unlink(target_file)
                    except OSError:
                        pass
                if os.path.isfile(mutations_file):
                    try:
                        os.unlink(mutations_file)
                    except OSError:
                        pass


    def test_tool_quirks_normalization_dedupe(self) -> None:
        """Verifies normalization deduplication of volatile tokens and file-agnostic rule generalization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_quirks = os.path.join(tmpdir, "test_quirks.md")
            Path(test_quirks).write_text("# Initial Tool Quirks\n", encoding="utf-8")

            # 1. Verify key normalization collapses numbers, backticked files, and volatile suffixes
            k1 = healer.normalize_reason_key(
                "run_command",
                "Token Economy Invariant: Command string length (4429) exceeds 4,000 characters. To prevent context bloat *(Auto-healed from failure ID 2058)*",
            )
            k2 = healer.normalize_reason_key(
                "run_command",
                "Command string length (4804) exceeds 4,000 characters. To prevent context bloat *(Auto-healed from failure ID 2059)*",
            )
            self.assertEqual(k1, k2, "Varying command lengths must normalize to the identical dedupe key")

            k_slice1 = healer.normalize_reason_key(
                "view_file",
                "Token Economy Invariant: Slice window (261 lines) on `lib/agy_tui_core.py` exceeds 250-line maximum.",
            )
            k_slice2 = healer.normalize_reason_key(
                "read_file",
                "Token Economy Invariant: Slice window (400 lines) on `validate-harness-tree.py` exceeds 250-line maximum.",
            )
            self.assertEqual(k_slice1, k_slice2, "Slice window failures across different files must normalize to identical key")

            # 2. Verify generalization produces file-agnostic rule texts
            gen_slice = healer.generalize_quirk_reason("Slice window (261 lines) on `lib/agy_tui_core.py` exceeds 250-line maximum. Narrow the slice window.")
            self.assertEqual(gen_slice, "Slice window exceeds 250-line maximum. Narrow the slice window.")
            self.assertNotIn("lib/agy_tui_core.py", gen_slice)

            gen_cmd = healer.generalize_quirk_reason("Command string length (4429) exceeds 4,000 characters. To prevent context bloat, write multi-line logic.")
            self.assertEqual(gen_cmd, "Command string length exceeds 4,000 characters. To prevent context bloat, write multi-line logic.")
            self.assertNotIn("4429", gen_cmd)

            gen_lock = healer.generalize_quirk_reason("Test-Immutability Lock: Adding .skip / @pytest.mark.skip to bypass failing tests is forbidden in `test_harness2_upgrades.py`.")
            self.assertIn("<file>", gen_lock)
            self.assertNotIn("test_harness2_upgrades.py", gen_lock)

            # 3. Apply repairs with four near-duplicate command length failures and two slice window failures
            clusters = {
                "tool_guidance": [
                    {"id": 1, "tool_name": "run_command", "reason": "Token Economy Invariant: Command string length (4429) exceeds 4,000 characters. *(Auto-healed from failure ID 1)*"},
                    {"id": 2, "tool_name": "run_command", "reason": "Token Economy Invariant: Command string length (4804) exceeds 4,000 characters. *(Auto-healed from failure ID 2)*"},
                    {"id": 3, "tool_name": "run_command", "reason": "Token Economy Invariant: Command string length (4111) exceeds 4,000 characters. *(Auto-healed from failure ID 3)*"},
                    {"id": 4, "tool_name": "run_command", "reason": "Token Economy Invariant: Command string length (4587) exceeds 4,000 characters. *(Auto-healed from failure ID 4)*"},
                    {"id": 5, "tool_name": "view_file", "reason": "Token Economy Invariant: Slice window (261 lines) on `lib/agy_tui_core.py` exceeds 250-line maximum."},
                    {"id": 6, "tool_name": "read_file", "reason": "Token Economy Invariant: Slice window (400 lines) on `validate-harness-tree.py` exceeds 250-line maximum."},
                ]
            }
            repaired_ids = set()
            healer.apply_deterministic_harness_repairs(clusters, tool_quirks_file=test_quirks, repaired_ids=repaired_ids)

            content = Path(test_quirks).read_text(encoding="utf-8")
            # Only 1 command length rule and 1 slice window rule should be present
            cmd_rules = [l for l in content.splitlines() if "Command string length" in l]
            slice_rules = [l for l in content.splitlines() if "Slice window exceeds" in l]
            self.assertEqual(len(cmd_rules), 1, f"Expected exactly 1 generalized command rule, got {len(cmd_rules)}")
            self.assertEqual(len(slice_rules), 1, f"Expected exactly 1 generalized slice rule, got {len(slice_rules)}")
            self.assertNotIn("4429", content)
            self.assertNotIn("4804", content)
            self.assertNotIn("261 lines", content)

    def test_tool_quirks_curated_preservation_and_cap(self) -> None:
        """Verifies curated rules and intro line are 100% preserved and excluded from 20-rule auto cap."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_quirks = os.path.join(tmpdir, "test_quirks.md")
            intro = "Execution invariants automatically captured and clustered by `auto-harness-healer.py`:"
            marker = "## Auto-Healed Tool Quirks (Level-3 Autonomous Loop)"
            curated_rule_1 = "- **`run_command` Quirk**: SWE-agent 50-Hit Search Flood Guard: Unbounded `rg` detected without limits. Pass `-m 50` or pipe to `head -n 50`."
            curated_rule_2 = "- **`view_file / read_file` Quirk**: Token Economy Invariant: Slice window exceeds 250-line maximum. Narrow the slice window (<= 250 lines)."
            curated_rule_3 = "- **`run_command` Quirk**: Command string length exceeds 4,000 chars. Write script or break into steps."

            initial_content = (
                "# Base Guidelines\n\n"
                f"{marker}\n\n"
                f"{intro}\n\n"
                f"{curated_rule_1}\n"
                f"{curated_rule_2}\n"
                f"{curated_rule_3}\n"
            )
            Path(test_quirks).write_text(initial_content, encoding="utf-8")

            # Ingest 25 distinct new failure rules to exceed the 20-item cap
            nato_words = [
                "alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel",
                "india", "juliet", "kilo", "lima", "mike", "november", "oscar", "papa",
                "quebec", "romeo", "sierra", "tango", "uniform", "victor", "whiskey", "xray", "yankee"
            ]
            failures = []
            for i, word in enumerate(nato_words, start=1):
                failures.append({
                    "id": 100 + i,
                    "tool_name": "run_command",
                    "reason": f"Custom unique tool violation {word} error signature",
                })
            clusters = {"tool_guidance": failures}
            repaired_ids = set()
            healer.apply_deterministic_harness_repairs(clusters, tool_quirks_file=test_quirks, repaired_ids=repaired_ids)

            updated = Path(test_quirks).read_text(encoding="utf-8")
            self.assertIn(marker, updated)
            self.assertIn(intro, updated, "Intro line must be preserved")
            self.assertIn(curated_rule_1, updated, "Curated rule 1 must be preserved")
            self.assertIn(curated_rule_2, updated, "Curated rule 2 must be preserved")
            self.assertIn(curated_rule_3, updated, "Curated rule 3 must be preserved")

            # Check that only auto rules (with failure ID) are capped at 20
            auto_rules = [
                l for l in updated.splitlines()
                if "(Auto-healed from failure ID" in l
            ]
            self.assertEqual(len(auto_rules), 20, f"Auto rules must be capped at 20, got {len(auto_rules)}")
            # Oldest auto rules (101-105) must have been dropped
            self.assertNotIn("failure ID 101", updated)
            self.assertNotIn("failure ID 105", updated)
            # Newest auto rule (125) must be present
            self.assertIn("failure ID 125", updated)

    def test_repo_tool_quirks_with_live_entries_dry_run(self) -> None:
        """Requirement 3: Verifies repo tool-quirks + 20 live entries yields curated + <= handful generalized new rules with no duplicates."""
        quirks_template_path = Path(__file__).resolve().parents[3] / "antigravity" / "guidelines" / "tool-quirks.md"

        live_sample_lines = [
            "- **`view_file / read_file` Quirk**: Slice Loop Breaker ACTIVATED: `stop_hook.py` has already had 3 sliced reads (duplicate slice loop). Further slicing is b *(Auto-healed from failure ID 291)*",
            "- **`run_command` Quirk**: The cd command is strictly prohibited in run_command. Use tool-native directory flags (e.g. git -C <dir>, npm --prefix <dir>, pytest <dir>, make -C <dir>) or absolute paths instead. *(Auto-healed from failure ID 294)*",
            "- **`edit_file` Quirk**: Test-Immutability Lock: Adding .skip / @pytest.mark.skip to bypass failing tests is forbidden in `test_harness2_upgrades *(Auto-healed from failure ID 317)*",
            "- **`run_command` Quirk**: Error-Stagnation Circuit Breaker: The last 3 command executions failed with the identical error signature. Stop blind tr *(Auto-healed from failure ID 339)*",
            "- **`run_command` Quirk**: Modern CLI Tool Invariant: Legacy `find` is strictly forbidden in Antigravity. Use `fd` instead (e.g. `fd 'pattern' path *(Auto-healed from failure ID 436)*",
            "- **`view_file / read_file` Quirk**: Token Economy Invariant: Slice window (251 lines) on `pre_tool_use_hook.py` exceeds 250-line maximum. Narrow the slice w *(Auto-healed from failure ID 449)*",
            "- **`run_command` Quirk**: Execution of sleep in run_command is strictly forbidden by token_economy rules. Use WaitMsBeforeAsync or the schedule to *(Auto-healed from failure ID 478)*",
            "- **`edit_file` Quirk**: Fix-The-Code-Not-The-Test Invariant: Role 'dev-be' is forbidden from deleting or weakening existing assert/expect lines  *(Auto-healed from failure ID 558)*",
            "- **`view_file / read_file` Quirk**: Scout-Block Gate (ClaudeKit): Traversing generated/vendor directory (node_modules) leaks tokens. Target source files ins *(Auto-healed from failure ID 799)*",
            "- **`run_command` Quirk**: Role Isolation Shell-Write Guard (pm-no-implementation.md): Non-builder session (Root Orchestrator (PM)) is strictly pro *(Auto-healed from failure ID 804)*",
            "- **`view_file / read_file` Quirk**: Token Economy Invariant: Slice window (261 lines) on `lib/agy_tui_core.py` exceeds 250-line maximum. Narrow the slice window *(Auto-healed from failure ID 853)*",
            "- **`view_file / read_file` Quirk**: Slice Loop Breaker ACTIVATED: `lib/agy_tui_core.py` has already had 6 sliced reads (reached 6-slice ceiling). Further slicin *(Auto-healed from failure ID 854)*",
            "- **`view_file / read_file` Quirk**: Slice Loop Breaker ACTIVATED: `recursive-ppc-engine.py` has already had 6 sliced reads (reached 6-slice ceiling). Furthe *(Auto-healed from failure ID 1254)*",
            "- **`view_file / read_file` Quirk**: Outline-First Monolithic File Guard: `test_codegraph.py` has 446 total lines (> 400 lines). Whole-file reading is blocke *(Auto-healed from failure ID 1418)*",
            "- **`run_command` Quirk**: Token Economy Invariant: SWE-agent 50-Hit Search Flood Guard: Unbounded `rg` detected without output limits. Specify out *(Auto-healed from failure ID 2057)*",
            "- **`run_command` Quirk**: Token Economy Invariant: Command string length (4429) exceeds 4,000 characters. To prevent context bloat, write multi-li *(Auto-healed from failure ID 2058)*",
            "- **`run_command` Quirk**: Token Economy Invariant: Command string length (4804) exceeds 4,000 characters. To prevent context bloat, write multi-li *(Auto-healed from failure ID 2059)*",
            "- **`run_command` Quirk**: Token Economy Invariant: Command string length (4111) exceeds 4,000 characters. To prevent context bloat, write multi-li *(Auto-healed from failure ID 2060)*",
            "- **`run_command` Quirk**: Token Economy Invariant: Command string length (4587) exceeds 4,000 characters. To prevent context bloat, write multi-li *(Auto-healed from failure ID 2062)*",
            "- **`view_file / read_file` Quirk**: Token Economy Invariant: Slice window (400 lines) on `validate-harness-tree.py` exceeds 250-line maximum. Narrow the sli *(Auto-healed from failure ID 2069)*",
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_quirks = os.path.join(tmpdir, "tool-quirks.md")
            raw_text = quirks_template_path.read_text(encoding="utf-8")
            clean_lines = [
                line for line in raw_text.splitlines()
                if "(Auto-healed from failure ID" not in line
            ]
            Path(tmp_quirks).write_text("\n".join(clean_lines) + "\n", encoding="utf-8")

            marker = "## Auto-Healed Tool Quirks (Level-3 Autonomous Loop)"

            failures = []
            for line in live_sample_lines:
                ls = line.strip()
                import re
                m = re.match(r"^-\s*\*\*(.+?)\*\*:\s*(.+)$", ls)
                if not m:
                    continue
                t_name = healer.extract_tool_name(m.group(1))
                r_text = m.group(2)
                id_m = re.search(r"\*\(Auto-healed from failure ID (\d+)\)\*", ls)
                fid = int(id_m.group(1)) if id_m else 0
                failures.append({"tool_name": t_name, "reason": r_text, "id": fid})

            self.assertEqual(len(failures), 20, f"Expected 20 live failure entries, got {len(failures)}")

            clusters = {"tool_guidance": failures}
            repaired_ids = set()
            healer.apply_deterministic_harness_repairs(clusters, tool_quirks_file=tmp_quirks, repaired_ids=repaired_ids)

            res_content = Path(tmp_quirks).read_text(encoding="utf-8")
            self.assertIn(marker, res_content)
            _, res_auto = res_content.split(marker, 1)

            curated_lines = []
            auto_lines = []
            for l in res_auto.splitlines():
                ls = l.strip()
                if ls.startswith("- **"):
                    if "(Auto-healed from failure ID" in ls:
                        auto_lines.append(ls)
                    else:
                        curated_lines.append(ls)

            self.assertEqual(len(curated_lines), 17, f"Expected 17 curated rules preserved, got {len(curated_lines)}")
            self.assertLessEqual(len(auto_lines), 5, f"Expected <= 5 auto rules, got {len(auto_lines)}")
            self.assertGreater(len(auto_lines), 0, "Must have at least 1 new rule admitted")

            sigs = set()
            for al in auto_lines:
                sig = healer.normalize_reason_key("tool", al)
                self.assertNotIn(sig, sigs, f"Duplicate rule detected: {al}")
                sigs.add(sig)

    def test_evaluate_trajectory_match_all_four_modes_and_role_contract(self) -> None:
        """Verifies normalize_trajectory_tool, evaluate_trajectory_match (4 modes), and stop_hook role contract."""
        dream_path = os.path.join(SCRIPTS_DIR, "dream-replay-simulator.py")
        dream_spec = importlib.util.spec_from_file_location("dream_replay_simulator", dream_path)
        dream = importlib.util.module_from_spec(dream_spec)
        dream_spec.loader.exec_module(dream)
        import stop_hook

        # 1. Tool normalization across CLI and IDE
        self.assertEqual(dream.normalize_trajectory_tool("view_file"), "read_file")
        self.assertEqual(dream.normalize_trajectory_tool("read_file"), "read_file")
        self.assertEqual(dream.normalize_trajectory_tool("write_to_file"), "write_file")
        self.assertEqual(dream.normalize_trajectory_tool("write_file"), "write_file")
        self.assertEqual(dream.normalize_trajectory_tool("replace_file_content"), "edit_file")
        self.assertEqual(dream.normalize_trajectory_tool("multi_replace_file_content"), "edit_file")
        self.assertEqual(dream.normalize_trajectory_tool("edit_file"), "edit_file")

        # 2. Strict mode
        strict_ok = dream.evaluate_trajectory_match(
            ["view_file", "replace_file_content", "run_command"],
            ["read_file", "edit_file", "run_command"],
            mode="strict",
        )
        self.assertTrue(strict_ok["matched"])
        self.assertEqual(strict_ok["mode"], "strict")
        self.assertEqual(strict_ok["score"], 1.0)
        self.assertEqual(strict_ok["missing_tools"], [])
        self.assertEqual(strict_ok["extra_tools"], [])

        strict_fail = dream.evaluate_trajectory_match(
            ["replace_file_content", "view_file"],
            ["read_file", "edit_file"],
            mode="strict",
        )
        self.assertFalse(strict_fail["matched"])
        self.assertLess(strict_fail["score"], 1.0)

        # 3. Unordered mode
        unordered_ok = dream.evaluate_trajectory_match(
            ["replace_file_content", "view_file"],
            ["read_file", "edit_file"],
            mode="unordered",
        )
        self.assertTrue(unordered_ok["matched"])
        self.assertEqual(unordered_ok["score"], 1.0)

        unordered_fail = dream.evaluate_trajectory_match(
            ["read_file"],
            ["read_file", "edit_file"],
            mode="unordered",
        )
        self.assertFalse(unordered_fail["matched"])
        self.assertEqual(unordered_fail["missing_tools"], ["edit_file"])

        # 4. Subset mode
        subset_ok = dream.evaluate_trajectory_match(
            ["view_file", "call_mcp_tool"],
            ["read_file", "call_mcp_tool", "search_web"],
            mode="subset",
        )
        self.assertTrue(subset_ok["matched"])
        self.assertEqual(subset_ok["extra_tools"], [])

        subset_fail = dream.evaluate_trajectory_match(
            ["view_file", "write_to_file"],
            ["read_file", "call_mcp_tool"],
            mode="subset",
        )
        self.assertFalse(subset_fail["matched"])
        self.assertEqual(subset_fail["extra_tools"], ["write_file"])

        # 5. Superset mode
        superset_ok = dream.evaluate_trajectory_match(
            ["view_file", "replace_file_content", "run_command"],
            ["edit_file", "run_command"],
            mode="superset",
        )
        self.assertTrue(superset_ok["matched"])
        self.assertEqual(superset_ok["missing_tools"], [])

        superset_fail = dream.evaluate_trajectory_match(
            ["view_file", "replace_file_content"],
            ["edit_file", "run_command"],
            mode="superset",
        )
        self.assertFalse(superset_fail["matched"])
        self.assertEqual(superset_fail["missing_tools"], ["run_command"])

        # 6. stop_hook._evaluate_role_trajectory_contract
        res_research_ok = stop_hook._evaluate_role_trajectory_contract(
            "research",
            ["view_file", "call_mcp_tool", "list_resources"],
        )
        self.assertTrue(res_research_ok["matched"])
        self.assertEqual(res_research_ok["mode"], "subset")

        res_research_bad = stop_hook._evaluate_role_trajectory_contract(
            "research",
            ["read_file", "edit_file"],
        )
        self.assertFalse(res_research_bad["matched"])
        self.assertIn("edit_file", res_research_bad["extra_tools"])

    def test_harness_golden_dataset_synthesis_and_dream_replay(self) -> None:
        """Verifies harness_golden_dataset synthesis on S0/S1/SPEC_GAMING_ATTEMPT and replay scoring."""
        dream_path = os.path.join(SCRIPTS_DIR, "dream-replay-simulator.py")
        dream_spec = importlib.util.spec_from_file_location("dream_replay_simulator", dream_path)
        dream = importlib.util.module_from_spec(dream_spec)
        dream_spec.loader.exec_module(dream)

        with tempfile.TemporaryDirectory() as tmpdir:
            db_file = os.path.join(tmpdir, "golden_test.sqlite")
            sentinel.init_harness_ledger(db_file)

            # Record S1 critical failure -> should synthesize golden dataset row
            recorded = sentinel.record_harness_failure(
                conv_id="conv-g1",
                failure_type="syntax_error",
                slug="proj-golden",
                tool_name="replace_file_content",
                reason="SyntaxError in app.py",
                severity_tier="S1_critical",
                db_path=db_file,
            )
            self.assertTrue(recorded)

            # Duplicate signature on same slug -> UNIQUE(slug, input_signature) deduplicates via INSERT OR IGNORE
            sentinel.record_harness_failure(
                conv_id="conv-g2",
                failure_type="syntax_error",
                slug="proj-golden",
                tool_name="edit_file",
                reason="SyntaxError in app.py",
                severity_tier="S1_critical",
                db_path=db_file,
            )

            # Record SPEC_GAMING_ATTEMPT with S2_major -> should also synthesize golden dataset row
            sentinel.record_harness_failure(
                conv_id="conv-g3",
                failure_type="test_lock_violation",
                slug="proj-golden",
                tool_name="write_to_file",
                reason="Test-Immutability Lock violation",
                severity_tier="S2_major",
                bug_category="SPEC_GAMING_ATTEMPT",
                db_path=db_file,
            )

            # Drain pending failure via auto-harness-healer -> also synthesizes golden dataset row
            pending_f = os.path.join(tmpdir, "pending_golden.jsonl")
            Path(pending_f).write_text(
                json.dumps({
                    "conv_id": "conv-g4",
                    "slug": "proj-golden",
                    "vertex": "skill",
                    "failure_type": "jev_loop",
                    "tool_name": "run_command",
                    "severity_tier": "S0_catastrophic",
                    "severity_weight": 1.0,
                    "reason": "Jev 3-strike loop",
                    "bug_category": "ASYNC_CONCURRENCY_LOCK",
                }) + "\n",
                encoding="utf-8",
            )
            conn = sqlite3.connect(db_file)
            healer.init_harness_tables(conn)
            healer.drain_pending_failures(conn, pending_path=pending_f)
            golden_rows = conn.execute("SELECT slug, failure_type, bug_category FROM harness_golden_dataset;").fetchall()
            conn.close()

            self.assertEqual(len(golden_rows), 3, f"Expected 3 unique golden rows, got {len(golden_rows)}")

            # Replay via run_dream_replay (?mode=ro)
            replay_res = dream.run_dream_replay(registry_db=db_file)
            self.assertEqual(replay_res["golden_dataset_count"], 3)
            self.assertEqual(replay_res["golden_pass_rate"], 1.0)

    def test_cli_ide_tool_canonicalization_in_sentinel_and_healer(self) -> None:
        """Verifies CLI/IDE tool parity across sentinel.classify_vertex and healer normalization."""
        # 1. sentinel.classify_vertex parity
        self.assertEqual(
            sentinel.classify_vertex("syntax_error", "write_file", "SyntaxError in foo.py"),
            sentinel.classify_vertex("syntax_error", "write_to_file", "SyntaxError in foo.py"),
        )
        self.assertEqual(
            sentinel.classify_vertex("denial", "edit_file", "Fix-The-Code-Not-The-Test Invariant"),
            sentinel.classify_vertex("denial", "replace_file_content", "Fix-The-Code-Not-The-Test Invariant"),
        )
        self.assertEqual(
            sentinel.classify_vertex("read_budget_strike", "read_file", "Three-Strike File Read Gate"),
            sentinel.classify_vertex("read_budget_strike", "view_file", "Three-Strike File Read Gate"),
        )

        # 2. healer.extract_tool_name preserves replace_file_content for self-test compatibility
        self.assertEqual(healer.extract_tool_name("replace_file_content"), "replace_file_content")

        # 3. healer.normalize_reason_key and get_quirk_semantic_family canonicalize edit/write tools
        k_edit = healer.normalize_reason_key("edit_file", "Test-Immutability Lock in `test_a.py`")
        k_repl = healer.normalize_reason_key("replace_file_content", "Test-Immutability Lock in `test_b.py`")
        k_mrepl = healer.normalize_reason_key("multi_replace_file_content", "Test-Immutability Lock in `test_c.py`")
        self.assertEqual(k_edit, k_repl)
        self.assertEqual(k_edit, k_mrepl)

        k_w1 = healer.normalize_reason_key("write_file", "Syntax error on write")
        k_w2 = healer.normalize_reason_key("write_to_file", "Syntax error on write")
        self.assertEqual(k_w1, k_w2)

        self.assertEqual(
            healer.get_quirk_semantic_family("replace_file_content", "Test-Immutability Lock"),
            "ef_test_immutability",
        )
        self.assertEqual(
            healer.get_quirk_semantic_family("multi_replace_file_content", "Fix-The-Code-Not-The-Test Invariant"),
            "ef_fix_the_code",
        )
        self.assertEqual(
            healer.get_quirk_semantic_family("write_to_file", "Test-Immutability Lock"),
            "ef_test_immutability",
        )


if __name__ == "__main__":
    unittest.main()
