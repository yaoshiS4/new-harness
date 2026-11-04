from __future__ import annotations

import json
from pathlib import Path

from context_health.server import (
    _extract_observation_target,
    _parse_transcript,
    distill_observation_buffer,
    infer_compact_schema,
    project_trajectory_toon,
    spillover_batch,
    spillover_large_payload,
)


def test_spillover_small_payload_stays_inline() -> None:
    data = "Short inline message"
    res = spillover_large_payload(content=data, tool_name="test_tool", max_chars=100)
    assert res["status"] == "inline"
    assert res["tool_name"] == "test_tool"
    assert res["chars"] == len(data)
    assert res["content"] == data
    assert res["schema"] == f"str[{len(data)}]"


def test_spillover_large_payload_spills_to_disk() -> None:
    large_dict = {"items": [f"item_{i}" for i in range(500)], "meta": "A" * 7000}
    serialized = json.dumps(large_dict)
    res = spillover_large_payload(content=serialized, tool_name="codegraph", max_chars=1000)

    assert res["status"] == "spilled"
    assert res["tool_name"] == "codegraph"
    assert res["original_chars"] == len(serialized)
    assert "spillover_path" in res
    assert len(res["sha"]) == 10
    assert "toon" in res
    assert "spillover[1]{tool,chars,sha,path}:" in res["toon"]
    assert "codegraph" in res["toon"]
    assert res["schema"].startswith("dict{items:list[500]<str")

    # Verify spillover file exists and content matches
    spill_path = Path(res["spillover_path"])
    assert spill_path.is_file()
    assert spill_path.read_text(encoding="utf-8") == serialized
    spill_path.unlink(missing_ok=True)


def test_infer_compact_schema_types() -> None:
    assert infer_compact_schema(None) == "null"
    assert infer_compact_schema(True) == "bool"
    assert infer_compact_schema(42) == "int"
    assert infer_compact_schema(3.14) == "float"
    assert infer_compact_schema("hello") == "str[5]"
    assert infer_compact_schema([1, 2, 3]) == "list[3]<int>"
    assert infer_compact_schema({"a": 1, "b": ["x", "y"]}) == "dict{a:int,b:list[2]<str[1]>}"


def test_spillover_batch_dual_threshold_largest_first() -> None:
    payloads = [
        {"tool_name": "small_1", "content": "A" * 2000},
        {"tool_name": "medium_2", "content": "B" * 5500},
        {"tool_name": "medium_3", "content": "C" * 5200},
        {"tool_name": "huge_4", "content": "D" * 7000},
    ]
    res = spillover_batch(payloads, max_single_chars=6000, max_batch_chars=12000)
    assert res["status"] == "batch_processed"
    assert res["total_original_chars"] == 19700
    assert res["spilled_count"] == 2
    assert res["total_inline_chars"] == 7200
    items = res["items"]
    assert items[0]["status"] == "inline"
    assert items[1]["status"] == "spilled"
    assert items[1]["eviction_reason"] == "batch_budget_exceeded"
    assert items[2]["status"] == "inline"
    assert items[3]["status"] == "spilled"

    for item in items:
        if "spillover_path" in item:
            Path(item["spillover_path"]).unlink(missing_ok=True)


def test_cli_read_edit_write_parity(tmp_path: Path) -> None:
    target_file = str(tmp_path / "src" / "app.py")
    transcript = tmp_path / "transcript.jsonl"
    steps = [
        {"tool_calls": [{"name": "read_file", "args": {"Path": target_file}}]},
        {"tool_calls": [{"name": "read_file", "args": {"Path": target_file}}]},
        {"tool_calls": [{"name": "edit_file", "args": {"Path": target_file}}]},
        {"tool_calls": [{"name": "read_file", "args": {"Path": target_file}}]},
        {"tool_calls": [{"name": "write_file", "args": {"Path": target_file}}]},
    ]
    transcript.write_text("\n".join(json.dumps(s) for s in steps) + "\n", encoding="utf-8")

    step_count, tool_dist, file_reads, err_count, _ = _parse_transcript(str(transcript))
    assert step_count == 5
    assert tool_dist["read_file"] == 3
    assert tool_dist["edit_file"] == 1
    assert tool_dist["write_file"] == 1
    assert file_reads.get(target_file, 0) == 0

    assert _extract_observation_target("read_file", {"Path": target_file}) == "app.py"
    assert _extract_observation_target("edit_file", {"Path": target_file}) == "app.py"
    assert _extract_observation_target("write_file", {"file_path": target_file}) == "app.py"

    distilled = distill_observation_buffer(
        conversation_id="cli_parity_test",
        transcript_path=str(transcript),
    )
    assert distilled["status"] == "ok"
    assert distilled["mutations_count"] == 2
    assert distilled["reads_count"] == 1
    Path(distilled["buffer_path"]).unlink(missing_ok=True)


def test_project_trajectory_toon_and_error_preservation(tmp_path: Path) -> None:
    missing = project_trajectory_toon(conversation_id="nonexistent_conv_999999")
    assert missing["status"] == "not_found"
    assert missing["toon"] == ""

    transcript = tmp_path / "transcript.jsonl"
    lines = [
        {
            "step_index": 0,
            "type": "USER_INPUT",
            "source": "USER_EXPLICIT",
            "status": "DONE",
            "content": "Fix the broken database migration",
        },
        {
            "step_index": 1,
            "type": "PLANNER_RESPONSE",
            "source": "MODEL",
            "status": "DONE",
            "tool_calls": [
                {"name": "read_file", "args": {"Path": "/repo/db/migrate.py"}},
            ],
        },
        {
            "step_index": 2,
            "type": "PLANNER_RESPONSE",
            "source": "MODEL",
            "status": "DONE",
            "tool_calls": [
                {"name": "invoke_subagent", "args": {"Role": "dev-be", "TypeName": "self"}},
            ],
        },
        {
            "step_index": 3,
            "type": "TOOL_OUTPUT",
            "source": "SYSTEM",
            "status": "ERROR",
            "exit_code": 1,
            "content": "SyntaxError: invalid syntax at migrate.py line 42",
        },
    ]
    for idx in range(4, 25):
        lines.append(
            {
                "step_index": idx,
                "type": "PLANNER_RESPONSE",
                "source": "MODEL",
                "status": "DONE",
                "tool_calls": [
                    {"name": "read_file", "args": {"Path": f"/repo/src/module_{idx}.py"}},
                ],
            }
        )
    transcript.write_text("\n".join(json.dumps(s) for s in lines) + "\n", encoding="utf-8")

    res = project_trajectory_toon(
        conversation_id="traj_test_conv",
        transcript_path=str(transcript),
        max_tokens=120,
    )
    assert res["status"] == "ok"
    assert res["conversation_id"] == "traj_test_conv"
    assert res["step_count"] == len(lines)
    assert res["est_tokens"] > 0
    assert res["toon"].startswith(f"trajectory[{len(lines)}]{{step,actor,tool,target,status,est_tokens}}:")
    assert len(res["toon"]) <= 120 * 4
    assert "ERROR" in res["toon"]
    assert "SyntaxError" in res["toon"]
    assert any(r["actor"] == "subagent:dev-be" for r in res["rows"])
