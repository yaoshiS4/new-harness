import json
import os
import tempfile
import pytest

from context_health.server import (
    _compute_transcript_token_stats,
    _mask_observations,
    _find_session_dir,
    get_session_health,
    compact_observations,
    commit_context_ledger,
    distill_observation_buffer,
)


def _create_synthetic_transcript(logs_dir: str, num_cycles: int = 8) -> str:
    transcript_p = os.path.join(logs_dir, "transcript.jsonl")
    steps = [
        {
            "step_index": 0,
            "source": "USER_EXPLICIT",
            "type": "USER_INPUT",
            "content": "Implement feature X across multiple files.",
        }
    ]

    for c in range(num_cycles):
        # Planner response with thinking and tool call
        p_step = {
            "step_index": len(steps),
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "thinking": f"Analyzing cycle {c} architecture and calculating dependencies.",
            "tool_calls": [
                {
                    "name": "view_file" if c % 2 == 0 else "run_command",
                    "args": {
                        "AbsolutePath": f"/workspace/src/module_{c}.ts",
                        "CommandLine": f"npm test -- -t 'module_{c}'",
                    },
                }
            ],
        }
        steps.append(p_step)

        # Bulky observation step
        lines_count = 50 + c * 10
        obs_content = "\n".join(f"Line {i}: data block payload for cycle {c} verification output" for i in range(lines_count))
        o_step = {
            "step_index": len(steps),
            "source": "MODEL",
            "type": "GENERIC",
            "content": obs_content,
        }
        steps.append(o_step)

    with open(transcript_p, "w", encoding="utf-8") as f:
        for s in steps:
            f.write(json.dumps(s) + "\n")

    return transcript_p


def test_token_stats_and_observation_masking():
    with tempfile.TemporaryDirectory() as tmp_brain:
        session_id = "test-dl4code-session"
        session_dir = os.path.join(tmp_brain, session_id)
        logs_dir = os.path.join(session_dir, ".system_generated", "logs")
        os.makedirs(logs_dir, exist_ok=True)
        transcript_p = _create_synthetic_transcript(logs_dir, num_cycles=8)

        # 1. Test token stats
        stats = _compute_transcript_token_stats(transcript_p)
        assert stats["observation_tokens"] > 0
        assert stats["reasoning_tokens"] > 0
        assert stats["observation_token_share"] > 0.50
        print("Token Stats:", stats)

        # 2. Test get_session_health integration
        health = get_session_health(session_id=session_id, brain_dir=tmp_brain)
        assert health["observation_masking_available"] is True
        assert "observation_token_share" in health
        assert "reasoning_token_share" in health
        assert health["observation_token_share"] == stats["observation_token_share"]
        assert "compact_observations" in health["guidance"]

        # 3. Test deterministic observation masking with keep_recent_turns=4 (dry run)
        res_dry = compact_observations(
            session_id=session_id,
            brain_dir=tmp_brain,
            keep_recent_turns=4,
            dry_run=True,
        )
        assert res_dry["status"] == "DRY_RUN"
        assert res_dry["keep_recent_turns"] == 4
        # 8 cycles total: first 4 masked (indices 0..3), last 4 preserved (indices 4..7)
        assert res_dry["masked_steps_count"] == 4
        assert float(res_dry["token_savings_pct"].replace("%", "")) > 30.0
        assert "[Masked Observation:" in res_dry["digest"]
        assert res_dry["output_file"] is None

        # 4. Test compact_observations dry_run=False
        res_write = compact_observations(
            session_id=session_id,
            brain_dir=tmp_brain,
            keep_recent_turns=4,
            dry_run=False,
        )
        assert res_write["status"] == "COMPACTED"
        assert res_write["output_file"] is not None
        assert os.path.isfile(res_write["output_file"])

        # Inspect masked transcript contents
        with open(res_write["output_file"], "r", encoding="utf-8") as f:
            masked_steps = [json.loads(l) for l in f if l.strip()]

        # Early observation steps should be masked
        early_obs = [s for s in masked_steps if s.get("observation_masked")]
        assert len(early_obs) == 4
        for o in early_obs:
            c = o["content"]
            assert c.startswith("[Masked Observation:")
            assert "sha256:" in c
            assert "lines" in c

        # Recent observation steps should remain untouched
        recent_obs = [s for s in masked_steps[len(masked_steps) - 8:] if s.get("type") == "GENERIC"]
        for r in recent_obs:
            assert not r.get("observation_masked", False)
            assert not r["content"].startswith("[Masked Observation:")

        print("Observation Masking Verification Succeeded!")


def test_commit_context_ledger_with_masked_digest(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp_proj:
        with tempfile.TemporaryDirectory() as tmp_brain:
            session_id = "test-ledger-session"
            session_dir = os.path.join(tmp_brain, session_id)
            logs_dir = os.path.join(session_dir, ".system_generated", "logs")
            os.makedirs(logs_dir, exist_ok=True)
            _create_synthetic_transcript(logs_dir, num_cycles=6)

            monkeypatch.setenv("ANTIGRAVITY_BRAIN_DIR", tmp_brain)

            res = commit_context_ledger(
                milestone="M1_OBSERVATION_MASKING",
                goals_completed=["Upgrade 4 implemented"],
                files_modified=["server.py"],
                active_constraints=["NeurIPS DL4Code 2025 compliant"],
                project_dir=tmp_proj,
                include_masked_digest=True,
            )

            assert res["status"] == "COMMITTED"
            ledger_file = res["ledger_path"]
            assert os.path.isfile(ledger_file)
            content = open(ledger_file).read()
            assert "Observation Masking Telemetry" in content
            assert "Compacted Observation Ledger" in content
            print("Commit Context Ledger with Observation Masking Passed!")


def test_distill_observation_buffer(monkeypatch):
    """Test prefix-stable observational memory distillation (Observer + Reflector)."""
    with tempfile.TemporaryDirectory() as tmp_brain:
        session_id = "test-distill-session"
        session_dir = os.path.join(tmp_brain, session_id)
        logs_dir = os.path.join(session_dir, ".system_generated", "logs")
        os.makedirs(logs_dir, exist_ok=True)
        transcript_p = _create_synthetic_transcript(logs_dir, num_cycles=8)

        # Distill observation buffer directly with transcript_path
        res = distill_observation_buffer(conversation_id=session_id, transcript_path=transcript_p)
        assert res["status"] == "ok"
        assert res["conversation_id"] == session_id
        assert os.path.isfile(res["buffer_path"])

        content = open(res["buffer_path"], "r", encoding="utf-8").read()
        assert "Observational Memory Buffer" in content
        assert "Mutations & State Decisions" in content
        assert "Verification Outcomes" in content
        assert "Key Files Read" in content
        assert res["compression_ratio"].endswith("x")

        # Test deduplication of repeated reads
        assert res["reads_count"] > 0
        assert res["verifications_count"] > 0

        # Test auto-lookup via ANTIGRAVITY_BRAIN_DIR
        monkeypatch.setenv("ANTIGRAVITY_BRAIN_DIR", tmp_brain)
        res_auto = distill_observation_buffer(conversation_id=session_id)
        assert res_auto["status"] == "ok"
        assert res_auto["transcript_path"] == transcript_p

        print("PASS: test_distill_observation_buffer")


def test_find_session_dir_strictly_bounded_to_custom_brain(monkeypatch):
    """Test Defect 1: _find_session_dir must never escape custom brain_dir to host CLI brain."""
    with tempfile.TemporaryDirectory() as td:
        tmp_brain = os.path.join(td, "custom_brain")
        os.makedirs(tmp_brain, exist_ok=True)

        # 1. Custom brain_dir with session_id that does not exist in tmp_brain
        res = _find_session_dir(tmp_brain, session_id="non-existent-session-id-12345")
        assert res is None, f"Expected None but escaped to {res}"

        # 2. Custom brain_dir with no session_id and empty directory -> must return None, not escape to host
        res_empty = _find_session_dir(tmp_brain)
        assert res_empty is None, f"Expected None on empty custom brain_dir but escaped to {res_empty}"

        # 3. Custom brain_dir with its own session directory -> must return target inside tmp_brain
        sess_dir = os.path.join(tmp_brain, "custom-session-abc")
        log_dir = os.path.join(sess_dir, ".system_generated", "logs")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "transcript.jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "PLANNER_RESPONSE", "tool_calls": []}) + "\n")

        found = _find_session_dir(tmp_brain, session_id="custom-session-abc")
        assert found == sess_dir

        # 4. Without session_id -> fallback to most recently modified inside custom brain
        found_recent = _find_session_dir(tmp_brain)
        assert found_recent == sess_dir


if __name__ == "__main__":
    test_token_stats_and_observation_masking()
    print("ALL OBSERVATION MASKING TESTS PASSED!")
