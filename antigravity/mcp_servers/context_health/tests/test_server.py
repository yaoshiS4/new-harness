import json
import os
from pathlib import Path
import tempfile
import pytest

from context_health.server import (
    _auto_detect_brain_dir,
    _find_session_dir,
    _find_transcript_file,
    _normalize_path,
    _parse_transcript,
    _calculate_health_score,
    get_session_health,
    check_read_budget,
    commit_context_ledger,
)


def test_auto_detect_brain_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test explicit dir
        assert _auto_detect_brain_dir(tmpdir) == os.path.abspath(tmpdir)

        # Test env var
        monkeypatch.setenv("ANTIGRAVITY_BRAIN_DIR", tmpdir)
        assert _auto_detect_brain_dir("") == os.path.abspath(tmpdir)


def test_normalize_path():
    assert _normalize_path('"/foo/bar/baz.py"') == "/foo/bar/baz.py"
    assert _normalize_path("'  /foo/bar/baz.py  '") == "/foo/bar/baz.py"
    assert _normalize_path("/foo/bar/../bar/baz.py") == "/foo/bar/baz.py"


def test_calculate_health_score():
    # Healthy case
    score, status, directive, repeated = _calculate_health_score(
        step_count=15,
        file_size_bytes=100_000,
        file_reads={"/a/b.py": 1, "/a/c.py": 2},
        error_count=0,
    )
    assert score == 100
    assert status == "HEALTHY"
    assert directive == "PROCEED"
    assert repeated == {}

    # Degraded case (approaching context budget threshold)
    score, status, directive, repeated = _calculate_health_score(
        step_count=50,
        file_size_bytes=700_000,
        file_reads={"/a/b.py": 3, "/a/c.py": 1},
        error_count=1,
    )
    assert 55 <= score < 80
    assert status == "DEGRADED"
    assert directive == "COMPACT_LEDGER"
    assert repeated == {"/a/b.py": 3}

    # Critical case (severe rot)
    score, status, directive, repeated = _calculate_health_score(
        step_count=100,
        file_size_bytes=2_000_000,
        file_reads={"/a/b.py": 10, "/a/c.py": 8},
        error_count=5,
    )
    assert score < 55
    assert status == "CRITICAL"
    assert directive == "MANDATE_ISOLATION"


def test_synthetic_session_workflow():
    with tempfile.TemporaryDirectory() as tmp_brain:
        session_id = "test-session-123"
        session_dir = os.path.join(tmp_brain, session_id)
        logs_dir = os.path.join(session_dir, ".system_generated", "logs")
        os.makedirs(logs_dir, exist_ok=True)
        transcript_p = os.path.join(logs_dir, "transcript.jsonl")

        # Create transcript steps
        steps = [
            {
                "step_index": 0,
                "source": "USER_EXPLICIT",
                "type": "USER_INPUT",
                "content": "Do task",
            },
            {
                "step_index": 1,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "tool_calls": [
                    {
                        "name": "view_file",
                        "args": {"AbsolutePath": "/workspace/src/foo.py"},
                    }
                ],
            },
            {
                "step_index": 2,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "tool_calls": [
                    {
                        "name": "view_file",
                        "args": {"AbsolutePath": "/workspace/src/foo.py"},
                    }
                ],
            },
            {
                "step_index": 3,
                "source": "MODEL",
                "type": "PLANNER_RESPONSE",
                "tool_calls": [
                    {
                        "name": "run_command",
                        "args": {"CommandLine": "npm test"},
                    }
                ],
            },
        ]
        with open(transcript_p, "w", encoding="utf-8") as f:
            for s in steps:
                f.write(json.dumps(s) + "\n")

        # Check session health
        health = get_session_health(session_id=session_id, brain_dir=tmp_brain)
        assert health["status"] == "HEALTHY"
        assert health["step_count"] == 4
        assert health["tool_distribution"]["view_file"] == 2
        assert health["tool_distribution"]["run_command"] == 1

        # Check read budget for foo.py (already read 2 times -> next read exceeds 3-strike)
        budget_foo = check_read_budget(
            file_path="/workspace/src/foo.py",
            session_id=session_id,
            brain_dir=tmp_brain,
        )
        assert budget_foo["allowed"] is False
        assert budget_foo["count"] == 2
        assert "Three-Strike" in budget_foo["mitigation"]

        # Check read budget for bar.py (0 reads -> allowed)
        budget_bar = check_read_budget(
            file_path="/workspace/src/bar.py",
            session_id=session_id,
            brain_dir=tmp_brain,
        )
        assert budget_bar["allowed"] is True
        assert budget_bar["count"] == 0


def test_commit_context_ledger():
    with tempfile.TemporaryDirectory() as tmp_proj:
        res = commit_context_ledger(
            milestone="Phase 1 Complete",
            goals_completed=["Built server.py", "Added unit tests"],
            files_modified=["mcp/context_health/server.py"],
            active_constraints=["3-strike limit", "Tier C recency pinning"],
            project_dir=tmp_proj,
        )
        assert res["status"] == "COMMITTED"
        ledger_file = os.path.join(tmp_proj, "docs", "CONTEXT_LEDGER.md")
        assert os.path.isfile(ledger_file)
        with open(ledger_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Phase 1 Complete" in content
        assert "Built server.py" in content
        assert "mcp/context_health/server.py" in content
        assert "Tier C recency pinning" in content


def test_relative_path_matching_and_edit_reset():
    with tempfile.TemporaryDirectory() as tmp_brain:
        session_id = "test-relative-session"
        session_dir = os.path.join(tmp_brain, session_id)
        logs_dir = os.path.join(session_dir, ".system_generated", "logs")
        os.makedirs(logs_dir, exist_ok=True)
        transcript_p = os.path.join(logs_dir, "transcript.jsonl")

        workspace_root = "/workspace/project"
        abs_target = f"{workspace_root}/src/components/MyCard.tsx"
        rel_target = "src/components/MyCard.tsx"

        # Step 1 & 2: read file twice using absolute path
        steps = [
            {
                "step_index": 0,
                "type": "PLANNER_RESPONSE",
                "tool_calls": [
                    {"name": "view_file", "args": {"AbsolutePath": abs_target}}
                ],
            },
            {
                "step_index": 1,
                "type": "PLANNER_RESPONSE",
                "tool_calls": [
                    {"name": "view_file", "args": {"AbsolutePath": abs_target}}
                ],
            },
        ]
        with open(transcript_p, "w", encoding="utf-8") as f:
            for s in steps:
                f.write(json.dumps(s) + "\n")

        # Query using RELATIVE path and cwd -> should correctly match 2 prior reads and deny
        res = check_read_budget(
            file_path=rel_target,
            session_id=session_id,
            brain_dir=tmp_brain,
            cwd=workspace_root,
        )
        assert res["allowed"] is False
        assert res["count"] == 2
        assert "Three-Strike" in res["mitigation"]

        # Now simulate an edit to the file
        edit_step = {
            "step_index": 2,
            "type": "PLANNER_RESPONSE",
            "tool_calls": [
                {
                    "name": "replace_file_content",
                    "args": {"TargetFile": abs_target, "ReplacementContent": "new code"},
                }
            ],
        }
        with open(transcript_p, "a", encoding="utf-8") as f:
            f.write(json.dumps(edit_step) + "\n")

        # Query again after edit -> counter should be reset to 0, allowed!
        res_after_edit = check_read_budget(
            file_path=rel_target,
            session_id=session_id,
            brain_dir=tmp_brain,
            cwd=workspace_root,
        )
        assert res_after_edit["allowed"] is True
        assert res_after_edit["count"] == 0


def test_slice_awareness():
    with tempfile.TemporaryDirectory() as tmp_brain:
        session_id = "test-slice-session"
        session_dir = os.path.join(tmp_brain, session_id)
        logs_dir = os.path.join(session_dir, ".system_generated", "logs")
        os.makedirs(logs_dir, exist_ok=True)
        transcript_p = os.path.join(logs_dir, "transcript.jsonl")

        file_path = "/workspace/project/src/BigFile.tsx"

        # Read disjoint slices of BigFile.tsx (lines 1-100, 101-200, 201-300)
        steps = [
            {
                "step_index": 0,
                "type": "PLANNER_RESPONSE",
                "tool_calls": [
                    {"name": "view_file", "args": {"AbsolutePath": file_path, "StartLine": 1, "EndLine": 100}}
                ],
            },
            {
                "step_index": 1,
                "type": "PLANNER_RESPONSE",
                "tool_calls": [
                    {"name": "view_file", "args": {"AbsolutePath": file_path, "StartLine": 101, "EndLine": 200}}
                ],
            },
            {
                "step_index": 2,
                "type": "PLANNER_RESPONSE",
                "tool_calls": [
                    {"name": "view_file", "args": {"AbsolutePath": file_path, "StartLine": 201, "EndLine": 300}}
                ],
            },
        ]
        with open(transcript_p, "w", encoding="utf-8") as f:
            for s in steps:
                f.write(json.dumps(s) + "\n")

        # Disjoint slice reads should NOT have triggered the 3-strike repeated full read lock
        res = check_read_budget(
            file_path=file_path,
            session_id=session_id,
            brain_dir=tmp_brain,
        )
        assert res["allowed"] is True
        assert res["count"] == 0


def test_commit_context_ledger_zero_tax_aliases_and_workspace_resolution(monkeypatch):
    import sqlite3

    orig_expanduser = os.path.expanduser

    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace_dir = os.path.join(tmp_dir, "my_project")
        os.makedirs(workspace_dir, exist_ok=True)

        res = commit_context_ledger(
            summary="Completed refactoring",
            decisions=["Use zero-tax alias", "Retain backward compatibility"],
            project_dir=workspace_dir,
            include_masked_digest=False,
        )
        assert res["status"] == "COMMITTED"
        assert res["milestone"] == "Completed refactoring"
        ledger_p = os.path.join(workspace_dir, "docs", "CONTEXT_LEDGER.md")
        assert os.path.isfile(ledger_p)
        content = open(ledger_p, encoding="utf-8").read()
        assert "Completed refactoring" in content
        assert "Use zero-tax alias" in content
        assert "Retain backward compatibility" in content

        workspace_dir2 = os.path.join(tmp_dir, "my_project2")
        os.makedirs(workspace_dir2, exist_ok=True)
        res_default = commit_context_ledger(
            project_dir=workspace_dir2,
            include_masked_digest=False,
        )
        assert res_default["status"] == "COMMITTED"
        assert res_default["milestone"] == "Session Checkpoint"

        db_p = os.path.join(tmp_dir, "conversation_summaries.db")
        conn = sqlite3.connect(db_p)
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE conversation_summaries (
                conversation_id TEXT PRIMARY KEY,
                workspace_uris TEXT,
                last_modified_time TIMESTAMP
            )"""
        )
        target_ws = os.path.join(tmp_dir, "resolved_ws")
        os.makedirs(target_ws, exist_ok=True)
        cur.execute(
            "INSERT INTO conversation_summaries VALUES (?, ?, datetime('now'))",
            ("conv-abc", json.dumps([f"file://{target_ws}"])),
        )
        conn.commit()
        conn.close()

        fake_mcp_cwd = os.path.join(tmp_dir, "mcp_servers", "context_health")
        os.makedirs(fake_mcp_cwd, exist_ok=True)
        monkeypatch.chdir(fake_mcp_cwd)
        monkeypatch.setattr(
            os.path,
            "expanduser",
            lambda p: db_p if "conversation_summaries.db" in p else orig_expanduser(p),
        )

        res_conv = commit_context_ledger(
            conversation_id="conv-abc",
            summary="Resolved via conv id",
            include_masked_digest=False,
        )
        assert res_conv["status"] == "COMMITTED"
        assert res_conv["project_dir"] == target_ws
        assert os.path.isfile(os.path.join(target_ws, "docs", "CONTEXT_LEDGER.md"))

        target_ws_latest = os.path.join(tmp_dir, "resolved_ws_latest")
        os.makedirs(target_ws_latest, exist_ok=True)
        conn = sqlite3.connect(db_p)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO conversation_summaries VALUES (?, ?, datetime('now', '+1 hour'))",
            ("conv-latest", json.dumps([f"file://{target_ws_latest}"])),
        )
        conn.commit()
        conn.close()

        res_latest = commit_context_ledger(
            summary="Resolved via latest",
            include_masked_digest=False,
        )
        assert res_latest["status"] == "COMMITTED"
        assert res_latest["project_dir"] == target_ws_latest
        assert os.path.isfile(os.path.join(target_ws_latest, "docs", "CONTEXT_LEDGER.md"))


def test_commit_context_ledger_fallback_when_no_workspace(monkeypatch):
    orig_expanduser = os.path.expanduser

    with tempfile.TemporaryDirectory() as tmp_home:
        monkeypatch.setenv("HOME", tmp_home)
        monkeypatch.setattr(
            os.path,
            "expanduser",
            lambda p: os.path.join(tmp_home, p[2:]) if p.startswith("~/") else (tmp_home if p == "~" else orig_expanduser(p)),
        )

        with tempfile.TemporaryDirectory(suffix="context_health") as fake_cwd:
            orig_cwd = os.getcwd()
            try:
                os.chdir(fake_cwd)
                res = commit_context_ledger(
                    summary="Fallback checkpoint",
                    include_masked_digest=False,
                )
                assert res["status"] == "COMMITTED"
                expected_dir = os.path.join(tmp_home, ".cache", "antigravity_context_ledger")
                expected_ledger = os.path.join(expected_dir, "CONTEXT_LEDGER.md")
                assert res["ledger_path"] == expected_ledger
                assert os.path.isfile(expected_ledger)
                content = Path(expected_ledger).read_text(encoding="utf-8")
                assert "Fallback checkpoint" in content
            finally:
                os.chdir(orig_cwd)


def test_get_session_health_and_compact_observations_conversation_id_alias():
    from context_health.server import compact_observations

    with tempfile.TemporaryDirectory() as tmp_brain:
        target_id = "conv-target-001"
        decoy_id = "conv-decoy-999"

        target_logs = os.path.join(tmp_brain, target_id, ".system_generated", "logs")
        decoy_logs = os.path.join(tmp_brain, decoy_id, ".system_generated", "logs")
        os.makedirs(target_logs, exist_ok=True)
        os.makedirs(decoy_logs, exist_ok=True)

        target_tp = os.path.join(target_logs, "transcript.jsonl")
        decoy_tp = os.path.join(decoy_logs, "transcript.jsonl")

        target_steps = [
            {
                "step_index": 0,
                "type": "PLANNER_RESPONSE",
                "tool_calls": [{"name": "view_file", "args": {"AbsolutePath": "/a/healthy.py"}}],
            },
            {"step_index": 1, "type": "GENERIC", "content": "line1\nline2\nline3\n" + ("x" * 160)},
            {
                "step_index": 2,
                "type": "PLANNER_RESPONSE",
                "tool_calls": [{"name": "view_file", "args": {"AbsolutePath": "/a/other.py"}}],
            },
            {"step_index": 3, "type": "GENERIC", "content": "ok"},
        ]
        with open(target_tp, "w", encoding="utf-8") as f:
            for s in target_steps:
                f.write(json.dumps(s) + "\n")

        decoy_steps = []
        for idx in range(60):
            decoy_steps.append(
                {
                    "step_index": idx * 2,
                    "type": "PLANNER_RESPONSE",
                    "status": "ERROR",
                    "tool_calls": [{"name": "view_file", "args": {"AbsolutePath": "/a/loop.py"}}],
                }
            )
            decoy_steps.append({"step_index": idx * 2 + 1, "type": "GENERIC", "content": "err\n" * 80})
        with open(decoy_tp, "w", encoding="utf-8") as f:
            for s in decoy_steps:
                f.write(json.dumps(s) + "\n")

        os.utime(os.path.join(tmp_brain, target_id), (1_700_000_000, 1_700_000_000))
        os.utime(target_tp, (1_700_000_000, 1_700_000_000))
        os.utime(os.path.join(tmp_brain, decoy_id), (1_700_000_500, 1_700_000_500))
        os.utime(decoy_tp, (1_700_000_500, 1_700_000_500))

        res_default = get_session_health(brain_dir=tmp_brain)
        assert res_default["session_id"] == decoy_id
        assert res_default["conversation_id"] == decoy_id
        assert res_default["status"] == "CRITICAL"

        res_alias = get_session_health(brain_dir=tmp_brain, conversation_id=target_id)
        assert res_alias["session_id"] == target_id
        assert res_alias["conversation_id"] == target_id
        assert res_alias["status"] == "HEALTHY"

        res_pos = get_session_health(target_id, tmp_brain)
        assert res_pos["session_id"] == target_id
        assert res_pos["conversation_id"] == target_id

        res_compact = compact_observations(
            brain_dir=tmp_brain,
            keep_recent_turns=1,
            dry_run=True,
            conversation_id=target_id,
        )
        assert res_compact["status"] == "DRY_RUN"
        assert res_compact["session_id"] == target_id
        assert res_compact["conversation_id"] == target_id
        assert res_compact["masked_steps_count"] == 1


def test_check_read_budget_conversation_id_alias():
    with tempfile.TemporaryDirectory() as tmp_brain:
        clean_id = "conv-clean-01"
        exhausted_id = "conv-exhausted-02"
        file_p = "/workspace/project/src/shared.py"

        clean_logs = os.path.join(tmp_brain, clean_id, ".system_generated", "logs")
        exhausted_logs = os.path.join(tmp_brain, exhausted_id, ".system_generated", "logs")
        os.makedirs(clean_logs, exist_ok=True)
        os.makedirs(exhausted_logs, exist_ok=True)

        clean_tp = os.path.join(clean_logs, "transcript.jsonl")
        exhausted_tp = os.path.join(exhausted_logs, "transcript.jsonl")

        with open(clean_tp, "w", encoding="utf-8") as f:
            f.write(json.dumps({"step_index": 0, "type": "USER_INPUT", "content": "hi"}) + "\n")

        with open(exhausted_tp, "w", encoding="utf-8") as f:
            for idx in range(3):
                f.write(
                    json.dumps(
                        {
                            "step_index": idx,
                            "type": "PLANNER_RESPONSE",
                            "tool_calls": [{"name": "view_file", "args": {"AbsolutePath": file_p}}],
                        }
                    )
                    + "\n"
                )

        os.utime(os.path.join(tmp_brain, clean_id), (1_700_000_000, 1_700_000_000))
        os.utime(clean_tp, (1_700_000_000, 1_700_000_000))
        os.utime(os.path.join(tmp_brain, exhausted_id), (1_700_000_500, 1_700_000_500))
        os.utime(exhausted_tp, (1_700_000_500, 1_700_000_500))

        res_clean = check_read_budget(file_path=file_p, brain_dir=tmp_brain, conversation_id=clean_id)
        assert res_clean["allowed"] is True
        assert res_clean["count"] == 0

        res_exhausted = check_read_budget(file_path=file_p, brain_dir=tmp_brain, conversation_id=exhausted_id)
        assert res_exhausted["allowed"] is False
        assert res_exhausted["count"] == 3

        res_positional = check_read_budget(file_p, clean_id, tmp_brain)
        assert res_positional["allowed"] is True


def test_commit_context_ledger_and_distill_observation_buffer_session_id_alias(monkeypatch):
    import sqlite3
    from context_health.server import distill_observation_buffer

    orig_expanduser = os.path.expanduser

    with tempfile.TemporaryDirectory() as tmp_home:
        monkeypatch.setenv("HOME", tmp_home)
        monkeypatch.setattr(
            os.path,
            "expanduser",
            lambda p: os.path.join(tmp_home, p[2:]) if p.startswith("~/") else (tmp_home if p == "~" else orig_expanduser(p)),
        )

        tmp_brain = os.path.join(tmp_home, "custom_brain")
        monkeypatch.setenv("ANTIGRAVITY_BRAIN_DIR", tmp_brain)

        alpha_id = "sess-alpha"
        latest_id = "sess-latest"
        alpha_logs = os.path.join(tmp_brain, alpha_id, ".system_generated", "logs")
        latest_logs = os.path.join(tmp_brain, latest_id, ".system_generated", "logs")
        os.makedirs(alpha_logs, exist_ok=True)
        os.makedirs(latest_logs, exist_ok=True)

        alpha_tp = os.path.join(alpha_logs, "transcript.jsonl")
        latest_tp = os.path.join(latest_logs, "transcript.jsonl")

        def _make_six_cycles(marker_file: str) -> list[dict]:
            items = []
            for idx in range(6):
                items.append(
                    {
                        "step_index": idx * 2,
                        "type": "PLANNER_RESPONSE",
                        "tool_calls": [
                            {
                                "name": "view_file",
                                "args": {
                                    "AbsolutePath": f"/src/{marker_file}",
                                    "Path": f"/src/{marker_file}",
                                },
                            }
                        ],
                    }
                )
                items.append(
                    {
                        "step_index": idx * 2 + 1,
                        "type": "GENERIC",
                        "content": f"contents of {marker_file}\nline2\nline3\n" + ("z" * 160),
                    }
                )
            return items

        with open(alpha_tp, "w", encoding="utf-8") as f:
            for s in _make_six_cycles("alpha_only_marker.py"):
                f.write(json.dumps(s) + "\n")
        with open(latest_tp, "w", encoding="utf-8") as f:
            for s in _make_six_cycles("latest_decoy_marker.py"):
                f.write(json.dumps(s) + "\n")

        os.utime(os.path.join(tmp_brain, alpha_id), (1_700_000_000, 1_700_000_000))
        os.utime(alpha_tp, (1_700_000_000, 1_700_000_000))
        os.utime(os.path.join(tmp_brain, latest_id), (1_700_000_500, 1_700_000_500))
        os.utime(latest_tp, (1_700_000_500, 1_700_000_500))

        cli_dir = os.path.join(tmp_home, ".gemini", "antigravity-cli")
        os.makedirs(cli_dir, exist_ok=True)
        db_p = os.path.join(cli_dir, "conversation_summaries.db")
        ws_alpha = os.path.join(tmp_home, "ws_alpha")
        ws_latest = os.path.join(tmp_home, "ws_latest")
        os.makedirs(ws_alpha, exist_ok=True)
        os.makedirs(ws_latest, exist_ok=True)

        conn = sqlite3.connect(db_p)
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE conversation_summaries (
                conversation_id TEXT PRIMARY KEY,
                workspace_uris TEXT,
                last_modified_time TIMESTAMP
            )"""
        )
        cur.execute(
            "INSERT INTO conversation_summaries VALUES (?, ?, datetime('now'))",
            (alpha_id, json.dumps([f"file://{ws_alpha}"])),
        )
        cur.execute(
            "INSERT INTO conversation_summaries VALUES (?, ?, datetime('now', '+1 hour'))",
            (latest_id, json.dumps([f"file://{ws_latest}"])),
        )
        conn.commit()
        conn.close()

        fake_mcp_cwd = os.path.join(tmp_home, "mcp_servers", "context_health")
        os.makedirs(fake_mcp_cwd, exist_ok=True)
        monkeypatch.chdir(fake_mcp_cwd)

        res_ledger = commit_context_ledger(
            milestone="Session Alias Verification",
            include_masked_digest=True,
            session_id=alpha_id,
        )
        assert res_ledger["status"] == "COMMITTED"
        assert res_ledger["project_dir"] == ws_alpha
        ledger_text = Path(res_ledger["ledger_path"]).read_text(encoding="utf-8")
        assert "alpha_only_marker.py" in ledger_text
        assert "latest_decoy_marker.py" not in ledger_text

        res_distill = distill_observation_buffer(session_id=alpha_id, max_entries=10)
        assert res_distill["status"] == "ok"
        assert res_distill["conversation_id"] == alpha_id
        assert res_distill["reads_count"] == 1

        empty_brain = os.path.join(tmp_home, "empty_brain")
        os.makedirs(empty_brain, exist_ok=True)
        monkeypatch.setenv("ANTIGRAVITY_BRAIN_DIR", empty_brain)

        fallback_id = "sess-cli-fallback"
        fallback_logs = os.path.join(cli_dir, "brain", fallback_id, ".system_generated", "logs")
        os.makedirs(fallback_logs, exist_ok=True)
        fallback_tp = os.path.join(fallback_logs, "transcript.jsonl")
        with open(fallback_tp, "w", encoding="utf-8") as f:
            for s in _make_six_cycles("fallback_marker.py"):
                f.write(json.dumps(s) + "\n")

        res_fb = distill_observation_buffer(session_id=fallback_id, max_entries=5)
        assert res_fb["status"] == "ok"
        assert res_fb["conversation_id"] == fallback_id

        res_missing = distill_observation_buffer()
        assert res_missing["status"] == "NOT_FOUND"


def test_compress_fatal_preserving_and_spillover_buried_fatal():
    from context_health.server import compress_fatal_preserving, spillover_large_payload

    fatal_line_67 = "2026-11-01T06:49:41Z FATAL: [db_pool.py:142] Unhandled deadlock in transaction commit"
    lines = []
    for idx in range(1, 151):
        if idx == 67:
            lines.append(fatal_line_67)
        else:
            lines.append(f"2026-11-01T06:49:{idx % 60:02d}Z INFO: [worker] routine heartbeat poll tick={idx} payload={'x' * 60}")

    large_payload = "\n".join(lines)
    comp = compress_fatal_preserving(large_payload, max_chars=2000)
    assert comp["fatal_lines_preserved"] == 1
    assert fatal_line_67 in comp["compressed_preview"]
    assert "middle-out compressed" in comp["compressed_preview"]

    spilled = spillover_large_payload(large_payload, tool_name="run_command", max_chars=2000)
    assert spilled["status"] == "spilled"
    assert spilled["fatal_lines_preserved"] == 1
    assert fatal_line_67 in spilled["compressed_preview"]
    sp_path = Path(spilled["spillover_path"])
    if sp_path.is_file():
        sp_path.unlink(missing_ok=True)





