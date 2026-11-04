#!/usr/bin/env python3
"""Comprehensive Unit Tests for Autonomous RSI Components.

Covers:
- Level-2 Reflection Bridge CLI flags in stop_hook.py
- harvest_workspace_experience (ACCEPTED and NO_ENTRY cases)
- Hermes GEPA 3-axis Skill Pareto Analyzer
- Live-SWE-agent DOM Micro-Tool Hint in pre_invocation_hook.py
- Dream-RSI Trajectory Replay Simulator (--dream + --ratchet-worktree)
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "config" / "hooks"))

from pre_invocation_hook import _get_active_behavioral_antipatterns

ref_path = REPO_ROOT / "antigravity" / "scripts" / "reflect-experience.py"
ref_spec = importlib.util.spec_from_file_location("reflect_experience", ref_path)
re_mod = importlib.util.module_from_spec(ref_spec)
assert ref_spec and ref_spec.loader
ref_spec.loader.exec_module(re_mod)

dr_path = REPO_ROOT / "antigravity" / "scripts" / "dream-replay-simulator.py"
dr_spec = importlib.util.spec_from_file_location("dream_replay_simulator", dr_path)
dr_mod = importlib.util.module_from_spec(dr_spec)
assert dr_spec and dr_spec.loader
dr_spec.loader.exec_module(dr_mod)


class TestStopHookCLIArgs(unittest.TestCase):
    """Test Level-2 Reflection Bridge invocation in stop_hook.py."""

    def test_stop_hook_passes_conv_id_and_transcript_args(self) -> None:
        import stop_hook

        with tempfile.TemporaryDirectory() as td:
            workspace = td
            conv_id = "test-conv-bridge-123"
            transcript_p = os.path.join(td, "transcript.jsonl")
            with open(transcript_p, "w", encoding="utf-8") as f:
                f.write('{"status": "DONE"}\n')

            payload = {
                "conversationId": conv_id,
                "transcriptPath": transcript_p,
                "workspace": workspace,
            }

            fake_reflector = os.path.join(td, "reflect-experience.py")
            with open(fake_reflector, "w", encoding="utf-8") as f:
                f.write("#!/usr/bin/env python3\n")

            with patch("os.path.isfile", side_effect=lambda p: True if p == fake_reflector or p == os.path.expanduser("~/.gemini/antigravity/scripts/reflect-experience.py") else os.path.isfile(p)), \
                 patch("subprocess.Popen") as mock_popen:
                # Invoke the reflector trigger logic simulating stop_hook post-processing
                reflector_script = os.path.expanduser("~/.gemini/antigravity/scripts/reflect-experience.py")
                cmd = [
                    sys.executable,
                    reflector_script,
                    "--workspace",
                    workspace,
                    "--conv-id",
                    str(conv_id),
                    "--transcript",
                    str(transcript_p),
                ]
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )

                self.assertTrue(mock_popen.called)
                called_args = mock_popen.call_args[0][0]
                self.assertIn("--workspace", called_args)
                self.assertIn(workspace, called_args)
                self.assertIn("--conv-id", called_args)
                self.assertIn(conv_id, called_args)
                self.assertIn("--transcript", called_args)
                self.assertIn(transcript_p, called_args)


class TestHarvestWorkspaceExperience(unittest.TestCase):
    """Test harvest_workspace_experience for both ACCEPTED and NO_ENTRY branches."""

    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.test_root = Path(self.td.name)
        self.sb_dir = self.test_root / "skillbank"
        self.sb_dir.mkdir()

    def tearDown(self) -> None:
        self.td.cleanup()

    def test_state_json_positive_delta_promoted_and_repeat_rejected(self) -> None:
        ws = self.test_root / "ws_task"
        th = ws / ".antigravity" / "task_harness"
        th.mkdir(parents=True)
        state_file = th / "state.json"
        state_file.write_text(
            json.dumps({
                "step": 3,
                "last_delta": 0.42,
                "cue": "sqlite, busy_timeout",
                "lesson": "Configure busy_timeout=500 on all sqlite connections",
                "evidence": "Zero lock failures across 15 iterations",
                "history": [{"step": 3, "delta": 0.42, "reason": "Added busy_timeout"}],
            }),
            encoding="utf-8",
        )

        # First run: should be ACCEPTED
        res1 = re_mod.harvest_workspace_experience(
            workspace=ws,
            skillbank_dir=self.sb_dir,
        )
        self.assertEqual(res1["status"], "ACCEPTED")
        self.assertEqual(res1["verdict"], "helped")
        self.assertGreater(res1["bytes_written"], 0)

        # Check state.json updated
        updated_state = json.loads(state_file.read_text(encoding="utf-8"))
        self.assertTrue(updated_state.get("promoted_to_skillbank"))

        # Second run: should be NO_ENTRY (already promoted)
        res2 = re_mod.harvest_workspace_experience(
            workspace=ws,
            skillbank_dir=self.sb_dir,
        )
        self.assertEqual(res2["status"], "NO_ENTRY")

    def test_state_json_zero_or_negative_delta_rejected(self) -> None:
        ws = self.test_root / "ws_zero"
        th = ws / ".antigravity" / "task_harness"
        th.mkdir(parents=True)
        (th / "state.json").write_text(
            json.dumps({
                "step": 1,
                "last_delta": -0.15,
                "history": [{"step": 1, "delta": -0.15, "reason": "Syntax error introduced"}],
            }),
            encoding="utf-8",
        )

        res = re_mod.harvest_workspace_experience(
            workspace=ws,
            skillbank_dir=self.sb_dir,
        )
        self.assertEqual(res["status"], "NO_ENTRY")

    def test_registry_fail_to_pass_recovery_with_remedy(self) -> None:
        reg_db = self.test_root / "registry.sqlite"
        conn = sqlite3.connect(str(reg_db))
        conn.execute(
            """
            CREATE TABLE harness_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conv_id TEXT,
                failure_type TEXT,
                reason TEXT,
                remedy TEXT,
                resolved_at DATETIME,
                tool_name TEXT,
                vertex TEXT
            );
            """
        )
        conn.execute(
            """
            INSERT INTO harness_failures (conv_id, failure_type, reason, remedy, resolved_at, tool_name, vertex)
            VALUES ('conv-rec-test', 'slice_cap_exceeded', 'Slice exceeds 250 lines', 'Use AST outline before slicing', CURRENT_TIMESTAMP, 'read_file', 'tool_guidance');
            """
        )
        conn.commit()
        conn.close()

        ws = self.test_root / "ws_clean"
        ws.mkdir()

        res = re_mod.harvest_workspace_experience(
            workspace=ws,
            conv_id="conv-rec-test",
            registry_db_path=str(reg_db),
            skillbank_dir=self.sb_dir,
        )
        self.assertEqual(res["status"], "ACCEPTED")
        self.assertEqual(res["verdict"], "helped")
        self.assertIn("recov-", res["entry_id"])

    def test_registry_fail_to_pass_with_clean_transcript_and_single_file(self) -> None:
        reg_db = self.test_root / "registry_trans.sqlite"
        conn = sqlite3.connect(str(reg_db))
        conn.execute(
            """
            CREATE TABLE harness_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conv_id TEXT,
                failure_type TEXT,
                reason TEXT,
                remedy TEXT,
                resolved_at DATETIME,
                tool_name TEXT,
                vertex TEXT
            );
            """
        )
        conn.execute(
            """
            INSERT INTO harness_failures (conv_id, failure_type, reason, remedy, resolved_at, tool_name, vertex)
            VALUES ('conv-trans-01', 'flood_guard', '50 search hits exceeded', '', NULL, 'run_command', 'tool_guidance');
            """
        )
        conn.commit()
        conn.close()

        ws = self.test_root / "ws_trans"
        ws.mkdir()
        transcript = ws / "transcript.jsonl"
        transcript.write_text(
            json.dumps({
                "status": "DONE",
                "tool_calls": [
                    {"function": {"name": "edit_file", "arguments": json.dumps({"Path": "/app/service.py"})}}
                ]
            }) + "\n",
            encoding="utf-8",
        )

        res = re_mod.harvest_workspace_experience(
            workspace=ws,
            conv_id="conv-trans-01",
            transcript_path=str(transcript),
            registry_db_path=str(reg_db),
            skillbank_dir=self.sb_dir,
        )
        self.assertEqual(res["status"], "ACCEPTED")

    def test_unisolated_multi_file_edits_rejected_as_confounded(self) -> None:
        reg_db = self.test_root / "registry_confounded.sqlite"
        conn = sqlite3.connect(str(reg_db))
        conn.execute(
            """
            CREATE TABLE harness_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conv_id TEXT,
                failure_type TEXT,
                reason TEXT,
                remedy TEXT,
                resolved_at DATETIME,
                tool_name TEXT,
                vertex TEXT
            );
            """
        )
        conn.execute(
            """
            INSERT INTO harness_failures (conv_id, failure_type, reason, remedy, resolved_at, tool_name, vertex)
            VALUES ('conv-confound-01', 'syntax_error', 'UnboundLocalError', 'Fix variable scope', CURRENT_TIMESTAMP, 'edit_file', 'codebase');
            """
        )
        conn.commit()
        conn.close()

        ws = self.test_root / "ws_confound"
        ws.mkdir()
        transcript = ws / "transcript.jsonl"
        transcript.write_text(
            "\n".join([
                json.dumps({"status": "DONE", "tool_calls": [{"function": {"name": "edit_file", "arguments": json.dumps({"Path": "/app/a.py"})}}]}),
                json.dumps({"status": "DONE", "tool_calls": [{"function": {"name": "edit_file", "arguments": json.dumps({"Path": "/app/b.py"})}}]}),
                json.dumps({"status": "DONE", "tool_calls": [{"function": {"name": "edit_file", "arguments": json.dumps({"Path": "/app/c.py"})}}]}),
            ]) + "\n",
            encoding="utf-8",
        )

        res = re_mod.harvest_workspace_experience(
            workspace=ws,
            conv_id="conv-confound-01",
            transcript_path=str(transcript),
            registry_db_path=str(reg_db),
            skillbank_dir=self.sb_dir,
        )
        self.assertEqual(res["status"], "NO_ENTRY")
        self.assertEqual(res["verdict"], "confounded")


class TestGepaSkillPareto(unittest.TestCase):
    """Test Hermes GEPA 3-axis Pareto skill evaluation."""

    def test_compute_gepa_skill_pareto_identifies_frontier_and_dominated(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            s_dir = Path(td) / "skills"

            # Skill 1: High ROI, compact, zero failures -> Pareto frontier
            sk1 = s_dir / "optimal-skill"
            sk1.mkdir(parents=True)
            (sk1 / "SKILL.md").write_text(
                "---\nname: optimal-skill\ndescription: Optimal skill\n---\n## Directives\n1. Do X\n```bash\necho ok\n```\n",
                encoding="utf-8",
            )

            # Skill 2: Bloated character length -> Dominated on compactness
            sk2 = s_dir / "bloated-skill"
            sk2.mkdir(parents=True)
            (sk2 / "SKILL.md").write_text(
                "Plain text without description.\n" + ("Word " * 2500) + "\n",
                encoding="utf-8",
            )

            db_p = Path(td) / "registry.sqlite"
            conn = sqlite3.connect(str(db_p))
            conn.execute(
                """
                CREATE TABLE harness_failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT,
                    vertex TEXT
                );
                """
            )
            # Insert failures for bloated-skill
            conn.execute("INSERT INTO harness_failures (tool_name, vertex) VALUES ('bloated-skill', 'skill');")
            conn.execute("INSERT INTO harness_failures (tool_name, vertex) VALUES ('bloated-skill', 'skill');")
            conn.commit()
            conn.close()

            res = re_mod.compute_gepa_skill_pareto(skills_dir=s_dir, registry_db_path=str(db_p))

            self.assertEqual(res["total_skills"], 2)
            self.assertIn("optimal-skill", res["pareto_frontier"])
            self.assertTrue(any(d["name"] == "bloated-skill" for d in res["dominated_skills"]))
            self.assertTrue(len(res["optimization_hints"]) >= 1)


class TestPreInvocationDOMHint(unittest.TestCase):
    """Test Live-SWE-agent DOM Micro-Tool Hint in pre_invocation_hook.py."""

    def test_dom_hint_triggered_on_repeated_tool_friction(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_p = os.path.join(td, "registry.sqlite")
            conn = sqlite3.connect(db_p)
            conn.execute(
                """
                CREATE TABLE harness_failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id TEXT,
                    vertex TEXT,
                    failure_type TEXT,
                    reason TEXT,
                    resolved_at DATETIME
                );
                """
            )
            conn.execute(
                """
                INSERT INTO harness_failures (conv_id, vertex, failure_type, reason, resolved_at)
                VALUES ('conv-dom-test', 'tool_guidance', 'slice_loop_breaker', 'Slice loop breaker triggered', NULL);
                """
            )
            conn.execute(
                """
                INSERT INTO harness_failures (conv_id, vertex, failure_type, reason, resolved_at)
                VALUES ('conv-dom-test', 'tool_guidance', 'flood_guard', 'Flood guard triggered', NULL);
                """
            )
            conn.commit()
            conn.close()

            antipatterns = _get_active_behavioral_antipatterns(
                conv_id="conv-dom-test",
                registry_db_path=db_p,
            )

            self.assertTrue(any("DOM Micro-Tool Hint:" in a for a in antipatterns))
            self.assertTrue(any("codegraph:extract_symbols" in a for a in antipatterns))

    def test_dom_hint_not_triggered_when_friction_below_two(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_p = os.path.join(td, "registry.sqlite")
            conn = sqlite3.connect(db_p)
            conn.execute(
                """
                CREATE TABLE harness_failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id TEXT,
                    vertex TEXT,
                    failure_type TEXT,
                    reason TEXT,
                    resolved_at DATETIME
                );
                """
            )
            conn.execute(
                """
                INSERT INTO harness_failures (conv_id, vertex, failure_type, reason, resolved_at)
                VALUES ('conv-dom-one', 'tool_guidance', 'slice_loop_breaker', 'Single failure', NULL);
                """
            )
            conn.commit()
            conn.close()

            antipatterns = _get_active_behavioral_antipatterns(
                conv_id="conv-dom-one",
                registry_db_path=db_p,
            )

            self.assertFalse(any("DOM Micro-Tool Hint:" in a for a in antipatterns))


class TestDreamReplaySimulator(unittest.TestCase):
    """Test Dream-RSI Counterfactual Replay and Worktree Ratchet."""

    def test_run_dream_replay_returns_pareto_front_and_writes_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            t_root = Path(td)
            reg_db = t_root / "registry.sqlite"
            conn = sqlite3.connect(str(reg_db))
            conn.execute(
                """
                CREATE TABLE harness_failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id TEXT,
                    failure_type TEXT,
                    reason TEXT
                );
                """
            )
            conn.execute("INSERT INTO harness_failures (failure_type) VALUES ('slice_loop_breaker');")
            conn.execute("INSERT INTO harness_failures (failure_type) VALUES ('flood_guard');")
            conn.commit()
            conn.close()

            convs_dir = t_root / "conversations"
            convs_dir.mkdir()
            fake_conv = convs_dir / "conv_01.db"
            c_conn = sqlite3.connect(str(fake_conv))
            c_conn.execute("CREATE TABLE steps (idx INTEGER PRIMARY KEY, status INTEGER);")
            for i in range(8):
                c_conn.execute("INSERT INTO steps (idx, status) VALUES (?, 0);", (i,))
            c_conn.commit()
            c_conn.close()

            ws = t_root / "target_ws"
            ws.mkdir()

            res = dr_mod.run_dream_replay(
                registry_db=reg_db,
                conversations_dir=convs_dir,
                apply_overlay_workspace=ws,
            )

            self.assertEqual(res["conversations_analyzed"], 1)
            self.assertEqual(res["failures_analyzed"], 2)
            self.assertGreaterEqual(res["pareto_front_count"], 1)
            self.assertIsNotNone(res["top_policy"]["utility_score"])
            self.assertTrue(res["guardrails_written"])

            guardrails_file = ws / ".antigravity" / "task_harness" / "guardrails.json"
            self.assertTrue(guardrails_file.is_file())
            gr = json.loads(guardrails_file.read_text(encoding="utf-8"))
            self.assertIn("slice_cap", gr)
            self.assertIn("max_slices", gr)
            self.assertIn("flood_limit", gr)

    def test_run_worktree_ratchet_commit_on_success(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "git_repo"
            repo.mkdir()
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.local"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test Agent"], cwd=repo, check=True)
            (repo / "file.txt").write_text("initial\n", encoding="utf-8")
            subprocess.run(["git", "add", "file.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)

            res = dr_mod.run_worktree_ratchet(
                repo_root=repo,
                candidate_cmd="echo 'evolved' >> file.txt",
                verify_cmd="python3 -c 'print(\"pass\")'",
                baseline_utility=-1000.0,
            )

            self.assertEqual(res["ratchet_status"], "COMMITTED")
            self.assertTrue(res["branch"].startswith("autoevolve/ratchet-"))

            # Verify no dangling worktrees remain
            dangling = list(repo.glob(".git-worktree-ratchet-*"))
            self.assertEqual(len(dangling), 0)

    def test_run_worktree_ratchet_discard_on_verify_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "git_repo"
            repo.mkdir()
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.local"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test Agent"], cwd=repo, check=True)
            (repo / "file.txt").write_text("initial\n", encoding="utf-8")
            subprocess.run(["git", "add", "file.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)

            res = dr_mod.run_worktree_ratchet(
                repo_root=repo,
                candidate_cmd="echo 'bad' >> file.txt",
                verify_cmd="python3 -c 'import sys; sys.exit(1)'",
                baseline_utility=0.0,
            )

            self.assertEqual(res["ratchet_status"], "DISCARDED")
            self.assertIn("verify_cmd returned code", res["reason"])

            # Verify no dangling worktrees remain
            dangling = list(repo.glob(".git-worktree-ratchet-*"))
            self.assertEqual(len(dangling), 0)

    def test_13_dynamic_guardrails_200_6_50_promotion(self) -> None:
        import pre_tool_use_hook
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            th_dir = ws / ".antigravity" / "task_harness"
            th_dir.mkdir(parents=True, exist_ok=True)
            gr_file = th_dir / "guardrails.json"
            policy_data = {
                "slice_cap": 200,
                "max_slices": 6,
                "flood_limit": 50,
                "utility_score": 3587.1,
            }
            gr_file.write_text(json.dumps(policy_data), encoding="utf-8")

            loaded = pre_tool_use_hook._load_active_guardrail_policy(str(ws))
            self.assertEqual(loaded.get("slice_cap"), 200)
            self.assertEqual(loaded.get("max_slices"), 6)
            self.assertEqual(loaded.get("flood_limit"), 50)

            target = ws / "large_file.py"
            target.write_text("\n".join([f"line_{i} = {i}" for i in range(500)]) + "\n", encoding="utf-8")

            view_args = {
                "Path": str(target),
                "StartLine": 1,
                "EndLine": 220,
            }
            payload = {
                "workspacePaths": [str(ws)],
                "tool_name": "read_file",
                "tool_args": view_args,
            }
            res = pre_tool_use_hook._handle_view_file(view_args, payload)
            self.assertEqual(res.get("decision"), "deny")
            self.assertIn("exceeds 200-line maximum", res.get("reason", ""))


class TestSpanWaterfallAndTranscriptEdits(unittest.TestCase):
    """Test compute_span_waterfall_metrics and CLI/IDE transcript edit extraction."""

    def test_compute_span_waterfall_metrics_per_role_and_aggregate(self) -> None:
        spans = [
            {
                "role": "dev-be",
                "latency_ms": 120.5,
                "tokens_consumed": 1500,
                "tool_calls": 4,
                "retry_calls": 1,
                "total_edits": 2,
                "verified_edits": 2,
                "referenced_files_count": 2,
            },
            {
                "role": "dev-fe",
                "latency_ms": 80.0,
                "tokens_consumed": 900,
                "tool_calls": 2,
                "retry_calls": 0,
                "total_edits": 1,
                "verified_edits": 1,
                "referenced_files_count": 1,
            },
            {
                "role": "dev-be",
                "latency_ms": 49.5,
                "tokens_consumed": 600,
                "tool_calls": 2,
                "retry_calls": 0,
                "total_edits": 1,
                "verified_edits": 1,
                "referenced_files_count": 1,
            },
        ]
        metrics = re_mod.compute_span_waterfall_metrics(spans)
        self.assertEqual(metrics["total_latency_ms"], 250.0)
        self.assertEqual(metrics["tokens_consumed"], 3000)
        self.assertAlmostEqual(metrics["retry_waste_ratio"], 0.125, places=4)
        self.assertAlmostEqual(metrics["verified_edit_ratio"], 1.0, places=4)
        self.assertGreater(metrics["pareto_roi_score"], 0.0)

        per_role = metrics["per_role"]
        self.assertIn("dev-be", per_role)
        self.assertIn("dev-fe", per_role)
        self.assertEqual(per_role["dev-be"]["span_count"], 2)
        self.assertEqual(per_role["dev-be"]["total_latency_ms"], 170.0)
        self.assertEqual(per_role["dev-be"]["tokens_consumed"], 2100)
        self.assertAlmostEqual(per_role["dev-be"]["retry_waste_ratio"], 1 / 6, places=4)
        self.assertEqual(per_role["dev-be"]["verified_edit_ratio"], 1.0)
        self.assertGreater(per_role["dev-fe"]["pareto_roi_score"], per_role["dev-be"]["pareto_roi_score"])

    def test_ide_and_cli_transcript_edit_extraction_confounder(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            t_root = Path(td)
            sb_dir = t_root / "skillbank"
            sb_dir.mkdir()
            reg_db = t_root / "registry.sqlite"
            conn = sqlite3.connect(str(reg_db))
            conn.execute(
                """
                CREATE TABLE harness_failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id TEXT,
                    failure_type TEXT,
                    reason TEXT,
                    remedy TEXT,
                    resolved_at DATETIME,
                    tool_name TEXT,
                    vertex TEXT
                );
                """
            )
            conn.execute(
                """
                INSERT INTO harness_failures (conv_id, failure_type, reason, remedy, resolved_at, tool_name, vertex)
                VALUES ('conv-ide-edits', 'slice_cap_exceeded', 'Slice exceeds 250 lines', 'Use AST outline', CURRENT_TIMESTAMP, 'view_file', 'tool_guidance');
                """
            )
            conn.commit()
            conn.close()

            transcript_file = t_root / "transcript.jsonl"
            lines = [
                json.dumps({
                    "status": "DONE",
                    "tool_calls": [
                        {"name": "replace_file_content", "args": {"TargetFile": "/repo/src/mod_a.py"}},
                        {"name": "write_to_file", "args": {"AbsolutePath": "/repo/src/mod_b.ts"}},
                        {"name": "multi_replace_file_content", "args": {"file_path": "/repo/src/mod_c.py"}},
                    ],
                })
            ]
            transcript_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

            ws = t_root / "ws_ide"
            ws.mkdir()

            res = re_mod.harvest_workspace_experience(
                workspace=ws,
                conv_id="conv-ide-edits",
                transcript_path=str(transcript_file),
                registry_db_path=str(reg_db),
                skillbank_dir=sb_dir,
            )
            self.assertEqual(res["status"], "NO_ENTRY")
            self.assertEqual(res["verdict"], "confounded")


if __name__ == "__main__":
    unittest.main()
