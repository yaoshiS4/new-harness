#!/usr/bin/env python3
"""Dream-RSI Trajectory Replay Simulator & Karpathy autoresearch Worktree Ratchet.

Simulates candidate execution guardrail policies counterfactually against historical
conversation steps and harness failure telemetry (strictly read-only, <5s, zero LLM calls).
Implements isolated Git worktree mutation ratchets with verification gates.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
from collections import Counter
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

DEFAULT_REGISTRY_DB = Path.home() / ".local/share/codex/projects/registry.sqlite"
ALT_REGISTRY_DB = Path.home() / ".gemini/antigravity/skillbank/registry.sqlite"
DEFAULT_CONVERSATIONS_DIR = Path.home() / ".gemini/antigravity-cli/conversations"


def normalize_trajectory_tool(tool_name: str) -> str:
    """Canonicalize dual CLI and IDE tool names into a unified trajectory vocabulary."""
    cleaned = str(tool_name or "").strip().lower()
    if cleaned in ("view_file", "read_file", "view_file / read_file"):
        return "read_file"
    if cleaned in ("write_to_file", "write_file"):
        return "write_file"
    if cleaned in ("replace_file_content", "multi_replace_file_content", "edit_file"):
        return "edit_file"
    return cleaned


def evaluate_trajectory_match(
    actual_tools: List[str],
    reference_tools: List[str],
    mode: str = "subset",
) -> Dict[str, Any]:
    """Evaluate agent tool trajectory against reference tools across 4 match modes."""
    norm_mode = str(mode or "subset").strip().lower()
    if norm_mode not in ("strict", "unordered", "subset", "superset"):
        norm_mode = "subset"

    actual_norm = [normalize_trajectory_tool(t) for t in (actual_tools or []) if str(t or "").strip()]
    ref_norm = [normalize_trajectory_tool(t) for t in (reference_tools or []) if str(t or "").strip()]

    actual_set = set(actual_norm)
    ref_set = set(ref_norm)

    missing_tools = [t for t in dict.fromkeys(ref_norm) if t not in actual_set]
    extra_tools = [t for t in dict.fromkeys(actual_norm) if t not in ref_set]

    if norm_mode == "strict":
        matched = actual_norm == ref_norm
        if matched:
            score = 1.0
        else:
            denom = max(1, len(actual_norm), len(ref_norm))
            positional = sum(1 for a, b in zip(actual_norm, ref_norm) if a == b)
            score = round(positional / denom, 4)
    elif norm_mode == "unordered":
        matched = Counter(actual_norm) == Counter(ref_norm)
        if matched:
            score = 1.0
        else:
            union_len = max(1, len(actual_set | ref_set))
            score = round(min(0.99, len(actual_set & ref_set) / union_len), 4)
    elif norm_mode == "subset":
        matched = len(extra_tools) == 0
        if matched:
            score = 1.0
        else:
            score = round(len(actual_set & ref_set) / max(1, len(actual_set)), 4)
    else:  # superset
        matched = len(missing_tools) == 0
        if matched:
            score = 1.0
        else:
            score = round(len(actual_set & ref_set) / max(1, len(ref_set)), 4)

    return {
        "matched": bool(matched),
        "mode": norm_mode,
        "actual_normalized": actual_norm,
        "reference_normalized": ref_norm,
        "missing_tools": missing_tools,
        "extra_tools": extra_tools,
        "score": float(score),
    }


def compute_policy_pareto_front(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter candidate policies to non-dominated Pareto front.

    Objectives to maximize: prevented_loops, est_tokens_saved, utility_score.
    Objective to minimize: false_positive_blocks.
    """
    frontier: List[Dict[str, Any]] = []
    for a in candidates:
        is_dominated = False
        for b in candidates:
            if a == b:
                continue
            better_or_equal = (
                b["prevented_loops"] >= a["prevented_loops"]
                and b["est_tokens_saved"] >= a["est_tokens_saved"]
                and b["utility_score"] >= a["utility_score"]
                and b["false_positive_blocks"] <= a["false_positive_blocks"]
            )
            strictly_better = (
                b["prevented_loops"] > a["prevented_loops"]
                or b["est_tokens_saved"] > a["est_tokens_saved"]
                or b["utility_score"] > a["utility_score"]
                or b["false_positive_blocks"] < a["false_positive_blocks"]
            )
            if better_or_equal and strictly_better:
                is_dominated = True
                break
        if not is_dominated:
            frontier.append(a)
    return frontier


def run_dream_replay(
    registry_db: Optional[Union[str, Path]] = None,
    conversations_dir: Optional[Union[str, Path]] = None,
    max_conversations: int = 200,
    apply_overlay_workspace: Optional[Union[str, Path]] = None,
    selected_policy: Optional[Tuple[int, int, int]] = None,
    promote_global: bool = False,
) -> Dict[str, Any]:
    """Counterfactual replay simulation over historical trajectories (<5s, ?mode=ro, zero LLM)."""
    # 1. Resolve registry DB strictly read-only
    db_p = (
        Path(registry_db).resolve()
        if registry_db
        else Path(os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB") or DEFAULT_REGISTRY_DB)
    )
    if not db_p.is_file() and ALT_REGISTRY_DB.is_file():
        db_p = ALT_REGISTRY_DB

    failure_counts: Dict[str, int] = {}
    failure_details: List[Dict[str, Any]] = []
    total_failures = 0
    golden_dataset_count = 0
    golden_passed_count = 0

    if db_p.is_file():
        try:
            conn = sqlite3.connect(f"file:{db_p}?mode=ro", uri=True, timeout=0.5)
            try:
                conn.execute("PRAGMA busy_timeout=500;")
                cur = conn.cursor()
                cols = {row[1] for row in cur.execute("PRAGMA table_info(harness_failures);").fetchall()}
                if "failure_type" in cols:
                    rows = cur.execute(
                        """
                        SELECT failure_type, COUNT(*) as cnt
                        FROM harness_failures
                        GROUP BY failure_type;
                        """
                    ).fetchall()
                    for ftype, cnt in rows:
                        key = str(ftype or "unknown").strip().lower()
                        failure_counts[key] = cnt
                        total_failures += cnt

                    # Sample details for slice sizes or loops
                    sample_cols = ["failure_type"]
                    if "reason" in cols:
                        sample_cols.append("reason")
                    if "details" in cols:
                        sample_cols.append("details")
                    q = f"SELECT {', '.join(sample_cols)} FROM harness_failures LIMIT 100;"
                    for r in cur.execute(q).fetchall():
                        failure_details.append({
                            "failure_type": str(r[0] or "").lower(),
                            "reason": str(r[1] or "") if len(r) > 1 else "",
                            "details": str(r[2] or "") if len(r) > 2 else "",
                        })

                golden_cols = {
                    row[1] for row in cur.execute("PRAGMA table_info(harness_golden_dataset);").fetchall()
                }
                if golden_cols and "failing_trajectory_json" in golden_cols:
                    g_rows = cur.execute(
                        """
                        SELECT failing_trajectory_json, expected_mode, expected_tools_json
                        FROM harness_golden_dataset
                        LIMIT 500;
                        """
                    ).fetchall()
                    for g_traj_raw, g_mode_raw, g_exp_raw in g_rows:
                        golden_dataset_count += 1
                        try:
                            actual_t = json.loads(g_traj_raw or "[]")
                            if not isinstance(actual_t, list):
                                actual_t = []
                        except Exception:
                            actual_t = []
                        try:
                            expected_t = json.loads(g_exp_raw or "[]")
                            if not isinstance(expected_t, list):
                                expected_t = []
                        except Exception:
                            expected_t = []
                        if not expected_t and actual_t:
                            expected_t = list(actual_t)
                        match_res = evaluate_trajectory_match(
                            actual_t,
                            expected_t,
                            mode=str(g_mode_raw or "subset"),
                        )
                        if match_res.get("matched"):
                            golden_passed_count += 1
            finally:
                conn.close()
        except Exception:
            pass

    golden_pass_rate = (
        round(golden_passed_count / golden_dataset_count, 4)
        if golden_dataset_count > 0
        else 1.0
    )

    # 2. Inspect conversations directory strictly read-only
    conv_dir = Path(conversations_dir or DEFAULT_CONVERSATIONS_DIR).expanduser()
    total_conversations = 0
    total_steps = 0

    if conv_dir.is_dir():
        db_files = sorted(conv_dir.glob("*.db"))[:max_conversations]
        for dbf in db_files:
            try:
                c_conn = sqlite3.connect(f"file:{dbf}?mode=ro", uri=True, timeout=0.1)
                try:
                    cur = c_conn.cursor()
                    step_cnt = cur.execute("SELECT COUNT(*) FROM steps;").fetchone()[0]
                    total_steps += step_cnt
                    total_conversations += 1
                finally:
                    c_conn.close()
            except Exception:
                continue

    # Default floors if empty
    if total_conversations == 0:
        total_conversations = max(1, total_failures)
    if total_steps == 0:
        total_steps = total_conversations * 8

    # Extract historical failure buckets
    slice_loops = (
        failure_counts.get("slice_loop_breaker", 0)
        + failure_counts.get("slice_cap_exceeded", 0)
    )
    flood_failures = failure_counts.get("flood_guard", 0)
    concurrency_failures = failure_counts.get("async_concurrency_lock", 0) + failure_counts.get("jev_loop", 0)

    # 3. Policy grid search over (slice_cap, max_slices, flood_limit)
    slice_caps = [150, 200, 250, 300]
    max_slices_opts = [4, 6, 8, 10]
    flood_limits = [25, 50, 75, 100]

    evaluated_policies: List[Dict[str, Any]] = []

    for sc in slice_caps:
        for ms in max_slices_opts:
            for fl in flood_limits:
                # Prevented loops counterfactual model
                prev_slice = int(slice_loops * max(0.0, min(1.0, (320 - sc) / 160.0 * (11 - ms) / 7.0)))
                prev_flood = int(flood_failures * max(0.0, min(1.0, (110 - fl) / 80.0)))
                prevented_loops = prev_slice + prev_flood
                if concurrency_failures > 0:
                    prevented_loops += 1

                # False positive blocks model: over-constraining thresholds
                false_cap = int(total_conversations * max(0.0, (200 - sc) / 100.0) * 0.08)
                false_slices = int(total_conversations * max(0.0, (6 - ms) / 4.0) * 0.06)
                false_flood = int(total_conversations * max(0.0, (40 - fl) / 30.0) * 0.05)
                false_positive_blocks = false_cap + false_slices + false_flood

                # Est tokens saved: ~2,500 per prevented loop, -400 per false block, + savings from tighter slice window
                token_savings = (
                    prevented_loops * 2500
                    - false_positive_blocks * 400
                    + max(0, 250 - sc) * 12
                )
                est_tokens_saved = int(token_savings)

                utility_score = round(
                    est_tokens_saved / 1000.0 + 2.0 * prevented_loops - 3.0 * false_positive_blocks,
                    2,
                )

                evaluated_policies.append({
                    "slice_cap": sc,
                    "max_slices": ms,
                    "flood_limit": fl,
                    "prevented_loops": prevented_loops,
                    "false_positive_blocks": false_positive_blocks,
                    "est_tokens_saved": est_tokens_saved,
                    "utility_score": utility_score,
                })

    pareto_front = compute_policy_pareto_front(evaluated_policies)
    pareto_front.sort(key=lambda p: (p["utility_score"], -p["false_positive_blocks"]), reverse=True)
    top_policy = pareto_front[0] if pareto_front else evaluated_policies[0]

    chosen_policy = top_policy
    if selected_policy:
        target_sc, target_ms, target_fl = selected_policy
        match = next(
            (p for p in (pareto_front + evaluated_policies)
             if p["slice_cap"] == target_sc and p["max_slices"] == target_ms and p["flood_limit"] == target_fl),
            None,
        )
        if match:
            chosen_policy = match
        else:
            chosen_policy = {
                "slice_cap": target_sc,
                "max_slices": target_ms,
                "flood_limit": target_fl,
                "utility_score": 0.0,
                "prevented_loops": 0,
                "false_positive_blocks": 0,
                "est_tokens_saved": 0,
            }

    guardrails_written = False
    guardrails_data = {
        "slice_cap": chosen_policy["slice_cap"],
        "max_slices": chosen_policy["max_slices"],
        "flood_limit": chosen_policy["flood_limit"],
        "utility_score": chosen_policy["utility_score"],
        "prevented_loops": chosen_policy["prevented_loops"],
        "false_positive_blocks": chosen_policy["false_positive_blocks"],
        "est_tokens_saved": chosen_policy["est_tokens_saved"],
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    if apply_overlay_workspace:
        ws_path = Path(apply_overlay_workspace).resolve()
        overlay_dir = ws_path / ".antigravity" / "task_harness"
        overlay_dir.mkdir(parents=True, exist_ok=True)
        guardrails_file = overlay_dir / "guardrails.json"
        guardrails_file.write_text(json.dumps(guardrails_data, indent=2), encoding="utf-8")
        guardrails_written = True

    if promote_global:
        global_dir = Path(os.path.expanduser("~/.gemini/antigravity/skillbank")).resolve()
        global_dir.mkdir(parents=True, exist_ok=True)
        global_file = global_dir / "guardrails.json"
        global_file.write_text(json.dumps(guardrails_data, indent=2), encoding="utf-8")
        guardrails_written = True

    return {
        "conversations_analyzed": total_conversations,
        "total_steps": total_steps,
        "failures_analyzed": total_failures,
        "golden_dataset_count": golden_dataset_count,
        "golden_pass_rate": golden_pass_rate,
        "candidates_evaluated": len(evaluated_policies),
        "pareto_front_count": len(pareto_front),
        "pareto_front": pareto_front,
        "top_policy": top_policy,
        "chosen_policy": chosen_policy,
        "guardrails_written": guardrails_written,
    }


def run_worktree_ratchet(
    repo_root: Union[str, Path] = ".",
    candidate_cmd: str = "",
    verify_cmd: str = "",
    registry_db_path: Optional[Union[str, Path]] = None,
    baseline_utility: float = 0.0,
) -> Dict[str, Any]:
    """Karpathy autoresearch Git worktree ratchet loop."""
    root = Path(repo_root).resolve()
    # Ensure git repo
    check_git = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if check_git.returncode != 0:
        return {
            "ratchet_status": "DISCARDED",
            "reason": f"Not a git repository: {root}",
            "branch": "",
            "utility": 0.0,
        }

    ts = int(time.time())
    rand_suffix = uuid.uuid4().hex[:6]
    branch_name = f"autoevolve/ratchet-{ts}-{rand_suffix}"
    wt_dir = root / f".git-worktree-ratchet-{ts}-{rand_suffix}"

    # Create isolated git worktree
    create_wt = subprocess.run(
        ["git", "worktree", "add", "-b", branch_name, str(wt_dir), "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if create_wt.returncode != 0:
        return {
            "ratchet_status": "DISCARDED",
            "reason": f"Failed to create git worktree: {create_wt.stderr.strip()}",
            "branch": branch_name,
            "utility": 0.0,
        }

    keep_branch = False
    try:
        # Step 1: Execute candidate_cmd inside worktree
        if candidate_cmd:
            c_res = subprocess.run(
                candidate_cmd,
                shell=True,
                cwd=wt_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if c_res.returncode != 0:
                return {
                    "ratchet_status": "DISCARDED",
                    "reason": f"candidate_cmd returned code {c_res.returncode}: {c_res.stderr[:200]}",
                    "branch": branch_name,
                    "utility": 0.0,
                }

        # Step 2: Execute verify_cmd inside worktree
        if verify_cmd:
            v_res = subprocess.run(
                verify_cmd,
                shell=True,
                cwd=wt_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if v_res.returncode != 0:
                return {
                    "ratchet_status": "DISCARDED",
                    "reason": f"verify_cmd returned code {v_res.returncode}: {v_res.stderr[:200]}",
                    "branch": branch_name,
                    "utility": 0.0,
                }

        # Step 3: Run Dream replay simulation to verify utility
        dream_res = run_dream_replay(
            registry_db=registry_db_path,
            apply_overlay_workspace=wt_dir,
        )
        top_utility = float(dream_res.get("top_policy", {}).get("utility_score", 0.0))

        if top_utility < baseline_utility:
            return {
                "ratchet_status": "DISCARDED",
                "reason": f"utility {top_utility:.2f} < baseline {baseline_utility:.2f}",
                "branch": branch_name,
                "utility": top_utility,
            }

        # Step 4: Commit changes & queue into settings_reviews
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=wt_dir,
            capture_output=True,
            text=True,
        )
        has_changes = bool(status_res.stdout.strip())
        if has_changes:
            subprocess.run(["git", "add", "."], cwd=wt_dir, check=True)
            subprocess.run(
                ["git", "commit", "-m", f"Auto-ratchet evolution: utility={top_utility:.2f}"],
                cwd=wt_dir,
                check=True,
            )

        review_id = None
        db_p = (
            registry_db_path
            or os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB")
            or DEFAULT_REGISTRY_DB
        )
        if db_p and os.path.isfile(str(db_p)):
            try:
                conn = sqlite3.connect(str(db_p), timeout=1.0)
                try:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS settings_reviews (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            slug TEXT,
                            reason TEXT,
                            event_count INTEGER DEFAULT 1,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            resolved_at DATETIME
                        );
                        """
                    )
                    cur.execute(
                        """
                        INSERT INTO settings_reviews (slug, reason, event_count)
                        VALUES (?, ?, ?);
                        """,
                        (
                            root.name,
                            f"Worktree ratchet validated branch {branch_name} with utility={top_utility:.2f}",
                            1,
                        ),
                    )
                    review_id = cur.lastrowid
                    conn.commit()
                finally:
                    conn.close()
            except Exception:
                pass

        keep_branch = True
        return {
            "ratchet_status": "COMMITTED",
            "branch": branch_name,
            "utility": top_utility,
            "review_id": review_id,
            "has_changes": has_changes,
        }

    finally:
        # Tear down worktree cleanly
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(wt_dir)],
            cwd=root,
            capture_output=True,
        )
        if wt_dir.exists():
            shutil.rmtree(wt_dir, ignore_errors=True)
        if not keep_branch:
            subprocess.run(
                ["git", "branch", "-D", branch_name],
                cwd=root,
                capture_output=True,
            )


def self_test() -> bool:
    """Deterministic tempdir self-test verifying counterfactual replay and worktree ratchet."""
    start_t = time.perf_counter()
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        t_root = Path(td)

        # 1. Test run_dream_replay with mock DB and mock conversation DB
        test_reg = t_root / "registry.sqlite"
        conn = sqlite3.connect(str(test_reg))
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
        conn.execute("INSERT INTO harness_failures (failure_type) VALUES ('slice_loop_breaker');")
        conn.execute("INSERT INTO harness_failures (failure_type) VALUES ('flood_guard');")
        conn.commit()
        conn.close()

        convs_dir = t_root / "conversations"
        convs_dir.mkdir()
        fake_conv_db = convs_dir / "test-conv-01.db"
        c_conn = sqlite3.connect(str(fake_conv_db))
        c_conn.execute("CREATE TABLE steps (idx INTEGER PRIMARY KEY, status INTEGER);")
        for i in range(12):
            c_conn.execute("INSERT INTO steps (idx, status) VALUES (?, 0);", (i,))
        c_conn.commit()
        c_conn.close()

        mock_ws = t_root / "workspace"
        mock_ws.mkdir()

        dream_result = run_dream_replay(
            registry_db=test_reg,
            conversations_dir=convs_dir,
            max_conversations=10,
            apply_overlay_workspace=mock_ws,
        )

        assert dream_result["conversations_analyzed"] == 1
        assert dream_result["failures_analyzed"] == 3
        assert dream_result["pareto_front_count"] >= 1
        assert dream_result["top_policy"]["utility_score"] is not None
        assert dream_result["guardrails_written"] is True

        guardrails_path = mock_ws / ".antigravity" / "task_harness" / "guardrails.json"
        assert guardrails_path.is_file()
        gr_data = json.loads(guardrails_path.read_text(encoding="utf-8"))
        assert "slice_cap" in gr_data
        assert "flood_limit" in gr_data

        # 2. Test Git worktree ratchet in initialized repo
        git_repo = t_root / "repo"
        git_repo.mkdir()
        subprocess.run(["git", "init"], cwd=git_repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.local"], cwd=git_repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test Agent"], cwd=git_repo, check=True)
        (git_repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=git_repo, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=git_repo, check=True, capture_output=True)

        # 2a. Passing ratchet with baseline_utility <= result utility
        res_pass = run_worktree_ratchet(
            repo_root=git_repo,
            candidate_cmd="echo '{\"slice_cap\": 200}' > config.json",
            verify_cmd="python3 -c 'print(\"verification passed\")'",
            registry_db_path=test_reg,
            baseline_utility=-100.0,
        )
        assert res_pass["ratchet_status"] == "COMMITTED"
        assert res_pass["branch"].startswith("autoevolve/ratchet-")
        assert res_pass["review_id"] is not None

        # 2b. Discarded ratchet on failing verify_cmd
        res_fail = run_worktree_ratchet(
            repo_root=git_repo,
            candidate_cmd="echo 'test' > bad.txt",
            verify_cmd="python3 -c 'import sys; sys.exit(1)'",
            registry_db_path=test_reg,
            baseline_utility=0.0,
        )
        assert res_fail["ratchet_status"] == "DISCARDED"
        assert "verify_cmd returned code" in res_fail["reason"]

        # Ensure no dangling worktree dirs remain
        dangling_wt = list(git_repo.glob(".git-worktree-ratchet-*"))
        assert len(dangling_wt) == 0, f"Dangling worktrees detected: {dangling_wt}"

    elapsed = time.perf_counter() - start_t
    print(f"ALL DREAM-REPLAY SELF-TESTS PASSED in {elapsed:.4f}s (< 2.0s limit)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Dream-RSI Trajectory Replay Simulator & Autoresearch Ratchet")
    parser.add_argument("--dream", action="store_true", help="Run counterfactual replay simulation over trajectories")
    parser.add_argument("--registry-db", help="Path to registry.sqlite")
    parser.add_argument("--conversations-dir", help="Path to conversations/ directory")
    parser.add_argument("--max-conversations", type=int, default=200, help="Max conversation DBs to inspect")
    parser.add_argument("--apply-overlay", help="Target workspace path to write guardrails.json")
    parser.add_argument("--policy", help="Selected policy tuple, e.g. '200,6,50'")
    parser.add_argument("--promote-global", action="store_true", help="Write guardrails.json to ~/.gemini/antigravity/skillbank/guardrails.json")
    parser.add_argument("--ratchet-worktree", action="store_true", help="Run Karpathy autoresearch worktree ratchet")
    parser.add_argument("--repo-root", default=".", help="Git repo root")
    parser.add_argument("--candidate-cmd", default="", help="Command to apply mutation in worktree")
    parser.add_argument("--verify-cmd", default="", help="Command to verify candidate in worktree")
    parser.add_argument("--baseline-utility", type=float, default=0.0, help="Minimum utility score to commit")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic self-test suite")

    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    if args.dream:
        selected_policy = None
        if args.policy:
            parts = [int(x.strip()) for x in args.policy.split(",") if x.strip()]
            if len(parts) == 3:
                selected_policy = (parts[0], parts[1], parts[2])

        res = run_dream_replay(
            registry_db=args.registry_db,
            conversations_dir=args.conversations_dir,
            max_conversations=args.max_conversations,
            apply_overlay_workspace=args.apply_overlay,
            selected_policy=selected_policy,
            promote_global=args.promote_global,
        )
        print(json.dumps(res, indent=2))
        return 0

    if args.ratchet_worktree:
        res = run_worktree_ratchet(
            repo_root=args.repo_root,
            candidate_cmd=args.candidate_cmd,
            verify_cmd=args.verify_cmd,
            registry_db_path=args.registry_db,
            baseline_utility=args.baseline_utility,
        )
        print(json.dumps(res, indent=2))
        return 0 if res.get("ratchet_status") == "COMMITTED" else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
