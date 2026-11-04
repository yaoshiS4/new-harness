# Context Health MCP Server Instructions

## Overview
Authoritative session context telemetry, JetBrains Research deterministic observation masking, Three-Strike read gate verification, and structured Context Codec ledger management for Antigravity sessions.

> [!IMPORTANT]
> **One-Shot MCP Execution (No 2-Turn Schema Inspection Tax)**:
> Always invoke directly using `call_mcp_tool` with `ServerName: "context_health"`. Never inspect `.json` schemas before calling.

---

## Core Tools (`call_mcp_tool`)

All session-scoped tools accept **`conversation_id` and `session_id` interchangeably** (`effective_id = session_id or conversation_id`).

### 1. `get_session_health`
Retrieve ground-truth cognitive health score, turn count, token utilization, and context rot telemetry for the current agent session.
```json
{
  "ServerName": "context_health",
  "ToolName": "get_session_health",
  "Arguments": {
    "conversation_id": "<conversation_id>",
    "session_id": "<conversation_id>",
    "brain_dir": ""
  }
}
```

### 2. `compact_observations`
Applies JetBrains Research (NeurIPS DL4Code 2025) deterministic observation masking to older transcript steps.
Replaces bulky tool observations older than `keep_recent_turns` with deterministic masked markers (`[Masked Observation: ... | sha256:...]`), cutting transcript token overhead by ~50% while preserving 100% of trajectory history.
```json
{
  "ServerName": "context_health",
  "ToolName": "compact_observations",
  "Arguments": {
    "conversation_id": "<conversation_id>",
    "session_id": "<conversation_id>",
    "keep_recent_turns": 4,
    "dry_run": false
  }
}
```

### 3. `check_read_budget`
Authoritative Three-Strike read gate backend. Checks whether a target file can be read again without violating read ceilings or causing context rot.
```json
{
  "ServerName": "context_health",
  "ToolName": "check_read_budget",
  "Arguments": {
    "file_path": "/absolute/path/to/target/file",
    "conversation_id": "<conversation_id>",
    "session_id": "<conversation_id>",
    "cwd": "/path/to/project/root"
  }
}
```

### 4. `commit_context_ledger`
Appends a structured Context Codec snapshot to `docs/CONTEXT_LEDGER.md` with concurrency lock awareness, tracking completed milestones, modified files, and active constraints.
```json
{
  "ServerName": "context_health",
  "ToolName": "commit_context_ledger",
  "Arguments": {
    "milestone": "<milestone_name_or_stage>",
    "goals_completed": [
      "<goal_1_description>",
      "<goal_2_description>"
    ],
    "files_modified": [
      "/path/to/modified_file_1",
      "/path/to/modified_file_2"
    ],
    "active_constraints": [
      "<constraint_1>",
      "<constraint_2>"
    ],
    "conversation_id": "<conversation_id>",
    "session_id": "<conversation_id>",
    "include_masked_digest": true,
    "project_dir": "/path/to/project/root"
  }
}
```

### 5. `distill_observation_buffer`
Compacts turn deltas (mutations, verifications, deduplicated reads) into a prefix-stable observation buffer (`~/.cache/antigravity_observations/{conversation_id}.md`).
```json
{
  "ServerName": "context_health",
  "ToolName": "distill_observation_buffer",
  "Arguments": {
    "conversation_id": "<conversation_id>",
    "session_id": "<conversation_id>",
    "max_entries": 20
  }
}
```

### 6. `project_trajectory_toon`
Projects a session `transcript.jsonl` into a compact chronological TOON trajectory table (`trajectory[N]{step,actor,tool,target,status,est_tokens}:`) truncated cleanly within `max_tokens * 4` characters while preserving error diagnostics.
```json
{
  "ServerName": "context_health",
  "ToolName": "project_trajectory_toon",
  "Arguments": {
    "conversation_id": "<conversation_id>",
    "transcript_path": "",
    "max_tokens": 1200
  }
}
```

---

## Usage Guidelines
- **Proactive Health Checks**: Invoke `get_session_health` when turn count approaches 20 or context rot is suspected.
- **Pre-Handoff Compaction**: Invoke `compact_observations` with `dry_run: false` before writing phase handoff checkpoints.
- **Trajectory Projection**: Invoke `project_trajectory_toon` for token-bounded TOON trajectory summaries across CLI and IDE sessions.
- **Read Verification**: If unsure whether a file has exceeded the 3-strike read limit, query `check_read_budget` before calling `view_file` or `read_file`.
- **Milestone Checkpointing**: Commit milestones to `docs/CONTEXT_LEDGER.md` using `commit_context_ledger` at the end of each major stage.
