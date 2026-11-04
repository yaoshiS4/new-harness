#!/usr/bin/env python3
"""Unit tests for Autonomous RSI Shard A components:
- Word-boundary concurrency lock classification in Sentinel
- Enum-first semantic family matching and quirk canonicalization
- Multi-slug per-project environment overlays
- MAP-Elites (slug, top_vertex) Pareto frontier isolation and pruning
- Receipt-linked efficacy verification
- Mendelian comparative trait distillation
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "antigravity" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Import auto_harness_healer via importlib
healer_path = str(SCRIPTS_DIR / "auto-harness-healer.py")
healer_spec = importlib.util.spec_from_file_location("auto_harness_healer", healer_path)
healer = importlib.util.module_from_spec(healer_spec)
healer_spec.loader.exec_module(healer)

# Import burn_rate_sentinel via importlib
sentinel_path = str(SCRIPTS_DIR / "burn-rate-sentinel.py")
sentinel_spec = importlib.util.spec_from_file_location("burn_rate_sentinel", sentinel_path)
sentinel = importlib.util.module_from_spec(sentinel_spec)
sentinel_spec.loader.exec_module(sentinel)


class TestRSIShardA(unittest.TestCase):
    """Verifies Shard A fixes and upgrades for the autonomous self-healing stack."""

    def test_burn_rate_sentinel_lock_word_boundary_and_non_misclassification(self) -> None:
        """Verifies word-boundary regex prevents 'blocked' from false-matching lock."""
        # Non-lock / blocked strings must return ""
        self.assertEqual(sentinel.classify_bug_category(message="blocked"), "")
        self.assertEqual(sentinel.classify_bug_category(message="tool call denied by pre-tool hook: command is blocked"), "")
        self.assertEqual(sentinel.classify_bug_category(reason="policy rule blocked execution"), "")
        self.assertEqual(sentinel.classify_bug_category(message="read_budget_lock activated"), "")
        self.assertEqual(sentinel.classify_bug_category(message="slice_loop_breaker activated"), "")

        # Valid concurrency lock signatures must return ASYNC_CONCURRENCY_LOCK
        self.assertEqual(sentinel.classify_bug_category(error_type="TimeoutError"), "ASYNC_CONCURRENCY_LOCK")
        self.assertEqual(sentinel.classify_bug_category(message="Deadlock detected on resource"), "ASYNC_CONCURRENCY_LOCK")
        self.assertEqual(sentinel.classify_bug_category(message="sqlite3.OperationalError: database is locked"), "ASYNC_CONCURRENCY_LOCK")
        self.assertEqual(sentinel.classify_bug_category(message="Acquire lock timeout"), "ASYNC_CONCURRENCY_LOCK")
        self.assertEqual(sentinel.classify_bug_category(message="mutex contention detected"), "ASYNC_CONCURRENCY_LOCK")
        self.assertEqual(sentinel.classify_bug_category(message="locking table row"), "ASYNC_CONCURRENCY_LOCK")

    def test_tool_quirks_file_path_and_clean_curated_rules(self) -> None:
        """Verifies tool-quirks.md registry path and preservation of exactly 17 curated rules."""
        quirks_path = REPO_ROOT / "antigravity" / "guidelines" / "tool-quirks.md"
        self.assertTrue(quirks_path.is_file(), "tool-quirks.md must exist")
        content = quirks_path.read_text(encoding="utf-8")

        # Check path modernization
        self.assertIn("~/.local/share/codex/projects/registry.sqlite", content)
        self.assertNotIn("~/.gemini/antigravity-cli/registry.sqlite", content)

        # Check Section marker and absence of auto-healed lines in repository template
        marker = "## Auto-Healed Tool Quirks (Level-3 Autonomous Loop)"
        self.assertIn(marker, content)
        _, auto_sec = content.split(marker, 1)

        curated_lines = []
        auto_lines = []
        for line in auto_sec.splitlines():
            ls = line.strip()
            if ls.startswith("- **"):
                if "(Auto-healed from failure ID" in ls:
                    auto_lines.append(ls)
                else:
                    curated_lines.append(ls)

        self.assertEqual(len(curated_lines), 17, f"Expected 17 curated rules, found {len(curated_lines)}")
        self.assertEqual(len(auto_lines), 0, "All auto-healed failure lines must be cleared from template")

    def test_enum_first_semantic_family_matching(self) -> None:
        """Verifies failure_type enum mapping in get_quirk_semantic_family."""
        # Enum-first mappings
        self.assertEqual(healer.get_quirk_semantic_family("run_command", "rg without limit", failure_type="flood_guard"), "rc_swe_rg")
        self.assertEqual(healer.get_quirk_semantic_family("run_command", "fd search", failure_type="flood_guard"), "rc_swe_fd")
        self.assertEqual(healer.get_quirk_semantic_family("view_file", "slice window too large", failure_type="slice_cap_exceeded"), "vf_slice_window")
        self.assertEqual(healer.get_quirk_semantic_family("read_file", "6 slices reached", failure_type="slice_loop_breaker"), "vf_slice_ceiling")
        self.assertEqual(healer.get_quirk_semantic_family("run_command", "grep forbidden", failure_type="legacy_cli_blocked"), "rc_legacy_cli")
        self.assertEqual(healer.get_quirk_semantic_family("manage_task", "status polling", failure_type="task_polling_blocked"), "mt_polling")
        self.assertEqual(healer.get_quirk_semantic_family("view_file", "three-strike read", failure_type="read_budget_strike"), "vf_slice_ceiling")
        self.assertEqual(healer.get_quirk_semantic_family("read_file", "three-strike rule", failure_type="read_budget_lock"), "vf_slice_ceiling")
        self.assertEqual(healer.get_quirk_semantic_family("invoke_subagent", "prompt 8000 chars", failure_type="subagent_prompt_overflow"), "subagent_prompt")

    def test_truncated_quirk_canonicalization_across_five_families(self) -> None:
        """Verifies generalize_quirk_reason expands mid-word cutoffs into complete grammatical sentences."""
        # 1. ef_test_immutability
        raw_immut = "Test-Immutability Lock: Adding .skip / @pytest.mark.skip to bypass failing tests is forbidden in `test_harness2_upgrades"
        gen_immut = healer.generalize_quirk_reason(raw_immut)
        self.assertIn("<file>.", gen_immut)
        self.assertNotIn("test_harness2_upgrades", gen_immut)
        self.assertTrue(gen_immut.endswith("."))

        # 2. rc_error_stagnation
        raw_stagn = "Error-Stagnation Circuit Breaker: The last 3 command executions failed with the identical error signature. Stop blind tr"
        gen_stagn = healer.generalize_quirk_reason(raw_stagn)
        self.assertIn("Stop blind trial-and-error and inspect the root cause first.", gen_stagn)
        self.assertFalse(gen_stagn.endswith("blind tr"))
        self.assertTrue(gen_stagn.endswith("first."))

        # 3. ef_fix_the_code
        raw_fix = "Fix-The-Code-Not-The-Test Invariant: Role 'dev-be' is forbidden from deleting or weakening existing assert/expect lines "
        gen_fix = healer.generalize_quirk_reason(raw_fix)
        self.assertIn("weakening existing assert/expect lines. Fix the code under test instead.", gen_fix)
        self.assertIn("Role is forbidden", gen_fix)

        # 4. vf_scout_block
        raw_scout = "Scout-Block Gate (ClaudeKit): Traversing generated/vendor directory (node_modules) leaks tokens. Target source files ins"
        gen_scout = healer.generalize_quirk_reason(raw_scout)
        self.assertIn("Target source files instead.", gen_scout)
        self.assertFalse(gen_scout.endswith("files ins"))
        self.assertTrue(gen_scout.endswith("instead."))

        # 5. rc_role_pm
        raw_pm = "Role Isolation Shell-Write Guard (pm-no-implementation.md): Non-builder session (Root Orchestrator (PM)) is strictly pro"
        gen_pm = healer.generalize_quirk_reason(raw_pm)
        self.assertIn("is strictly prohibited from mutating application source code via shell write.", gen_pm)
        self.assertFalse(gen_pm.endswith("strictly pro"))
        self.assertTrue(gen_pm.endswith("write."))

        # Backward compatibility with exact tested strings
        gen_slice = healer.generalize_quirk_reason("Slice window (261 lines) on `lib/agy_tui_core.py` exceeds 250-line maximum. Narrow the slice window.")
        self.assertEqual(gen_slice, "Slice window exceeds 250-line maximum. Narrow the slice window.")

        gen_cmd = healer.generalize_quirk_reason("Command string length (4429) exceeds 4,000 characters. To prevent context bloat, write multi-line logic.")
        self.assertEqual(gen_cmd, "Command string length exceeds 4,000 characters. To prevent context bloat, write multi-line logic.")

    def test_multi_slug_per_project_overlays(self) -> None:
        """Verifies distinct offending project slugs each receive dedicated environment overlays."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_overlays = os.path.join(tmpdir, "env_overlays")
            tmp_quirks = os.path.join(tmpdir, "tool-quirks.md")
            Path(tmp_quirks).write_text("# Quirks Base\n", encoding="utf-8")

            clusters = {
                "tool_guidance": [],
                "codebase": [
                    {
                        "id": 101,
                        "slug": "project_alpha",
                        "vertex": "codebase",
                        "failure_type": "type_error",
                        "bug_category": "TYPE_CONTRACT_MISMATCH",
                        "reason": "Property 'userId' does not exist on type 'SessionContext'.",
                    },
                    {
                        "id": 102,
                        "slug": "project_beta",
                        "vertex": "codebase",
                        "failure_type": "import_error",
                        "bug_category": "IMPORT_DEPENDENCY_GAP",
                        "reason": "ModuleNotFoundError: No module named 'fastapi_cache'.",
                    },
                ],
            }

            repaired_ids = set()
            repairs = healer.apply_deterministic_harness_repairs(
                clusters,
                tool_quirks_file=tmp_quirks,
                active_slug="global",
                env_overlays_dir=tmp_overlays,
                repaired_ids=repaired_ids,
            )

            # Both alpha and beta overlay files must exist
            alpha_path = Path(tmp_overlays) / "project_alpha.md"
            beta_path = Path(tmp_overlays) / "project_beta.md"
            self.assertTrue(alpha_path.is_file(), "project_alpha.md must be generated")
            self.assertTrue(beta_path.is_file(), "project_beta.md must be generated")

            # Check contents
            alpha_text = alpha_path.read_text(encoding="utf-8")
            beta_text = beta_path.read_text(encoding="utf-8")
            self.assertIn("TYPE_CONTRACT_MISMATCH", alpha_text)
            self.assertIn("userId", alpha_text)
            self.assertIn("IMPORT_DEPENDENCY_GAP", beta_text)
            self.assertIn("fastapi_cache", beta_text)

            # Check resolved IDs collected across all slugs
            self.assertIn(101, repaired_ids)
            self.assertIn(102, repaired_ids)

    def test_map_elites_niche_scoping_and_pareto_dominance(self) -> None:
        """Verifies MAP-Elites (slug, top_vertex) coexistence and within-niche dominance pruning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "test_pareto.sqlite")
            conn = sqlite3.connect(test_db)
            healer.init_harness_tables(conn)

            # Insert c1 in niche (alpha_proj, hook)
            c1 = {"func_score": 1.0, "sec_score": 1.0, "token_score": 0.70}
            r1 = healer.update_pareto_archive(conn, slug="alpha_proj", objectives=c1, top_vertex="hook")
            self.assertTrue(r1["admitted"])

            # Insert c2 in distinct niche (alpha_proj, tool_guidance) with lower token_score
            c2 = {"func_score": 1.0, "sec_score": 1.0, "token_score": 0.65}
            r2 = healer.update_pareto_archive(conn, slug="alpha_proj", objectives=c2, top_vertex="tool_guidance")
            self.assertTrue(r2["admitted"], "Different vertex niche must not be dominated by hook candidate")

            # Verify both c1 and c2 are active on frontier
            active_rows = conn.execute(
                "SELECT id, top_vertex, is_pareto_front FROM harness_pareto_archive WHERE slug = 'alpha_proj';"
            ).fetchall()
            self.assertEqual(len(active_rows), 2)
            self.assertTrue(all(r[2] == 1 for r in active_rows))

            # Insert c3 in niche (alpha_proj, hook) with higher token_score (0.85 > 0.70)
            c3 = {"func_score": 1.0, "sec_score": 1.0, "token_score": 0.85}
            r3 = healer.update_pareto_archive(conn, slug="alpha_proj", objectives=c3, top_vertex="hook")
            self.assertTrue(r3["admitted"])
            self.assertEqual(r3["pruned_ids"], [active_rows[0][0]])

            # Verify c1 pruned (is_pareto_front = 0), c3 active (1), and c2 still active (1)
            final_rows = conn.execute(
                "SELECT id, top_vertex, is_pareto_front FROM harness_pareto_archive WHERE slug = 'alpha_proj' ORDER BY id ASC;"
            ).fetchall()
            self.assertEqual(len(final_rows), 3)
            self.assertEqual(final_rows[0][2], 0, "c1 must be pruned")
            self.assertEqual(final_rows[1][2], 1, "c2 must remain active in tool_guidance niche")
            self.assertEqual(final_rows[2][2], 1, "c3 must be active in hook niche")

    def test_evaluate_pareto_objectives_repaired_count_and_receipt_delta(self) -> None:
        """Verifies evaluate_pareto_objectives mathematical weighting for repairs and receipt deltas."""
        # Baseline zero repair & zero delta
        obj_base = healer.evaluate_pareto_objectives({}, sandbox_ok=True, repaired_count=0, receipt_delta=0.0)
        self.assertEqual(obj_base["func_score"], 1.0)
        self.assertEqual(obj_base["sec_score"], 1.0)

        # Sandbox fail overrides func_score to 0.0
        obj_fail = healer.evaluate_pareto_objectives({}, sandbox_ok=False, repaired_count=5, receipt_delta=0.2)
        self.assertEqual(obj_fail["func_score"], 0.0)

        # Positive repairs and positive delta
        obj_boost = healer.evaluate_pareto_objectives({}, sandbox_ok=True, repaired_count=3, receipt_delta=0.10)
        # func_score = 1.0 + min(0.25, 0.15) + min(0.25, 0.10) = 1.25
        self.assertEqual(obj_boost["func_score"], 1.25)

        # Negative delta with zero repairs
        obj_pen = healer.evaluate_pareto_objectives({}, sandbox_ok=True, repaired_count=0, receipt_delta=-0.15)
        # func_score = 1.0 + 0.0 + (-0.15) = 0.85
        self.assertEqual(obj_pen["func_score"], 0.85)

        # Ceilings and floors
        obj_ceil = healer.evaluate_pareto_objectives({}, sandbox_ok=True, repaired_count=10, receipt_delta=0.50)
        self.assertEqual(obj_ceil["func_score"], 1.5)

    def test_verify_receipt_linked_efficacy(self) -> None:
        """Verifies verify_receipt_linked_efficacy computes pre/post failure rates and updates archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "test_receipts.sqlite")
            conn = sqlite3.connect(test_db)
            healer.init_harness_tables(conn)

            # Insert baseline failure events (created_at = '2026-01-01 10:00:00')
            conn.execute(
                """
                INSERT INTO harness_failures (conv_id, slug, vertex, failure_type, reason, created_at)
                VALUES
                  ('s1', 'proj_receipt', 'tool_guidance', 'slice_cap_exceeded', 'slice error', '2026-01-01 10:00:00'),
                  ('s1', 'proj_receipt', 'tool_guidance', 'slice_cap_exceeded', 'slice error 2', '2026-01-01 10:05:00'),
                  ('s2', 'proj_receipt', 'tool_guidance', 'slice_cap_exceeded', 'slice error 3', '2026-01-01 11:00:00');
                """
            )

            # Insert pareto archive candidate (created_at = '2026-01-01 12:00:00')
            conn.execute(
                """
                INSERT INTO harness_pareto_archive (
                    slug, top_vertex, func_score, sec_score, token_score, is_pareto_front, created_at
                ) VALUES ('proj_receipt', 'tool_guidance', 1.0, 1.0, 0.85, 1, '2026-01-01 12:00:00');
                """
            )

            # Insert post-heal failure events (only 1 failure in session s3; failure rate drops from 3/2=1.5 to 1/1=1.0)
            conn.execute(
                """
                INSERT INTO harness_failures (conv_id, slug, vertex, failure_type, reason, created_at)
                VALUES ('s3', 'proj_receipt', 'tool_guidance', 'slice_cap_exceeded', 'slice error 4', '2026-01-01 13:00:00');
                """
            )
            conn.commit()

            results = healer.verify_receipt_linked_efficacy(conn)
            self.assertEqual(len(results), 1)
            row_id = next(iter(results))
            self.assertEqual(results[row_id]["baseline"], 1.5)
            self.assertEqual(results[row_id]["post_convs"], 1)
            # Delta = (1.5 - 1.0) / 1.5 = +0.3333 -> capped at 0.25
            self.assertEqual(results[row_id]["delta"], 0.25)

            # Check DB updated
            row = conn.execute("SELECT receipt_baseline_rate, receipt_eval_sessions, receipt_delta FROM harness_pareto_archive WHERE id = ?;", (row_id,)).fetchone()
            self.assertEqual(row[0], 1.5)
            self.assertEqual(row[1], 1)
            self.assertEqual(row[2], 0.25)

    def test_distill_mendelian_comparative_traits(self) -> None:
        """Verifies distill_mendelian_comparative_traits generates [MGM Contrast] directives from multi-session traits and remedies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_db = os.path.join(tmpdir, "test_mgm.sqlite")
            tmp_overlays = os.path.join(tmpdir, "overlays")
            conn = sqlite3.connect(test_db)
            healer.init_harness_tables(conn)

            # Insert systemic failure across 2 distinct sessions s1 and s2
            conn.execute(
                """
                INSERT INTO harness_failures (conv_id, slug, vertex, failure_type, bug_category, reason, remedy)
                VALUES
                  ('s1', 'proj_mgm', 'tool_guidance', 'slice_cap_exceeded', 'BOUNDARY_INDEX_ERROR', 'Slice window 300 lines exceeds cap', ''),
                  ('s2', 'proj_mgm', 'tool_guidance', 'slice_cap_exceeded', 'BOUNDARY_INDEX_ERROR', 'Slice window 400 lines exceeds cap', 'Pass StartLine: 1, EndLine: 200 explicitly');
                """
            )
            conn.commit()

            clusters = {
                "tool_guidance": [
                    {"id": 1, "slug": "proj_mgm", "vertex": "tool_guidance", "failure_type": "slice_cap_exceeded", "reason": "Slice window 300 lines exceeds cap"}
                ]
            }

            traits_by_slug = healer.distill_mendelian_comparative_traits(conn, clusters)
            self.assertIn("proj_mgm", traits_by_slug)
            directives = traits_by_slug["proj_mgm"]
            self.assertTrue(len(directives) >= 1)
            self.assertIn("[MGM Contrast]", directives[0])
            self.assertIn("slice_cap_exceeded", directives[0])
            self.assertIn("Pass StartLine: 1, EndLine: 200 explicitly", directives[0])

            # Verify write_env_harness_overlay renders the MGM directive
            overlay_path = healer.write_env_harness_overlay("proj_mgm", clusters, env_overlays_dir=tmp_overlays, mgm_directives=directives)
            content = Path(overlay_path).read_text(encoding="utf-8")
            self.assertIn("[MGM Contrast]", content)
            self.assertIn("Pass StartLine: 1, EndLine: 200 explicitly", content)


if __name__ == "__main__":
    unittest.main()
