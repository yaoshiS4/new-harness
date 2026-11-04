import json
import os
from pathlib import Path
import subprocess
import tempfile


def test_subagent_turn_one_grounding():
    repo_hook = Path(__file__).resolve().parents[4] / "config" / "hooks" / "pre_invocation_hook.py"
    hook_path = str(repo_hook) if repo_hook.is_file() else os.path.expanduser("~/.gemini/config/hooks/pre_invocation_hook.py")

    with tempfile.TemporaryDirectory(prefix="test_ws_") as tmp_ws:
        workspace = tmp_ws
        slug = os.path.basename(workspace)
        env = dict(os.environ, ANTIGRAVITY_SESSION_STATES_DIR=tmp_ws)

        # Test 1: Subagent Turn 1 Grounding Capsule
        subagent_turn_1_payload = {
            "invocationNum": 1,
            "workspacePaths": [workspace],
            "conversationId": "subagent-test-conv-001",
            "transcript": [
                {
                    "source": "SYSTEM",
                    "type": "SYSTEM_MESSAGE",
                    "content": "You are the Stage 5/6 Specialist Backend Builder (Role: 'dev-be') for Shard WS-3.",
                }
            ],
        }

        p = subprocess.run(
            ["python3", hook_path],
            input=json.dumps(subagent_turn_1_payload),
            text=True,
            capture_output=True,
            env=env,
        )
        assert p.returncode == 0, f"Hook exited with code {p.returncode}: {p.stderr}"
        res = json.loads(p.stdout.strip())
        inject_steps = res.get("injectSteps", [])
        assert len(inject_steps) > 0, f"Expected injected capsule, got {res}"
        msg = inject_steps[0].get("ephemeralMessage", "")

        print("=== Subagent Capsule Output ===")
        print(msg)
        print("================================")

        assert f"[Subagent Turn-1 Grounding Capsule - {slug}]" in msg
        assert "Key Memory Seeds (registry.sqlite)" in msg
        assert "Core GraphDB Triples (graph.sqlite, is_current=1)" in msg

        # Verify token bound (<= 350 tokens; 1 token ~ 4 characters)
        approx_tokens = len(msg) // 4
        print(f"Capsule length: {len(msg)} chars, approx {approx_tokens} tokens")
        assert approx_tokens <= 350, f"Capsule exceeded 350 tokens: {approx_tokens}"

        # Test 2: Subagent Turn 2 (should NOT inject capsule)
        subagent_turn_2_payload = {
            "invocationNum": 2,
            "workspacePaths": [workspace],
            "conversationId": "subagent-test-conv-001",
            "transcript": [
                {
                    "source": "SYSTEM",
                    "type": "SYSTEM_MESSAGE",
                    "content": "You are the Stage 5/6 Specialist Backend Builder (Role: 'dev-be') for Shard WS-3.",
                }
            ],
        }
        p2 = subprocess.run(
            ["python3", hook_path],
            input=json.dumps(subagent_turn_2_payload),
            text=True,
            capture_output=True,
            env=env,
        )
        assert p2.returncode == 0
        res2 = json.loads(p2.stdout.strip())
        # No milestone, no alerts -> injectSteps should be empty
        assert len(res2.get("injectSteps", [])) == 0, f"Turn 2 should be empty, got {res2}"

        # Test 3: Root Orchestrator Turn 1 (should inject Active Knowledge Grounding, not subagent capsule)
        root_turn_1_payload = {
            "invocationNum": 1,
            "workspacePaths": [workspace],
            "conversationId": "root-test-conv-001",
            "transcript": [
                {
                    "source": "USER_EXPLICIT",
                    "type": "USER_INPUT",
                    "content": "User request for root orchestrator",
                }
            ],
        }
        p3 = subprocess.run(
            ["python3", hook_path],
            input=json.dumps(root_turn_1_payload),
            text=True,
            capture_output=True,
            env=env,
        )
        assert p3.returncode == 0
        res3 = json.loads(p3.stdout.strip())
        msg3 = res3.get("injectSteps", [])[0].get("ephemeralMessage", "")
        assert f"[Active Knowledge Grounding - {slug}]" in msg3
        assert "[Subagent Turn-1 Grounding Capsule" not in msg3

        print("ALL SUBAGENT GROUNDING TESTS PASSED!")


if __name__ == "__main__":
    test_subagent_turn_one_grounding()
