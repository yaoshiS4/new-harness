---
name: context-rot-prevention
description: Prevents context rot and monitors cognitive token health at phase boundaries or high context thresholds.
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# Context Rot Prevention Skill

## Purpose
Prevent degradation of agent reasoning and task fidelity as context grows, grounded in empirical LLM research (Liu et al. 2023, Xia et al. 2026). Leverages `context_health` and `codegraph` MCP tools for proactive budget monitoring, AST structural inspection, and deterministic Observation Masking.

> [!IMPORTANT]
> **One-Shot MCP Execution (No 2-Turn Schema Inspection Tax)**:
> Always invoke directly using MCP tools (`mcp__<server>__<tool>`). Never inspect `.json` schemas before calling. Never use hallucinated legacy function names.

---

## Three-Strike Read Budget Enforcement

The mechanical PreToolUse hook enforces the Three-Strike Read Budget Gate natively.
- **Mechanical Gate**: After 2 whole-file reads or when reading a file repeatedly without intermediate edits, further whole reads are blocked.
- **When Blocked**:
  - **STOP `Read` immediately**. Do not micro-slice or re-read.
  - Check read budget and health via `context_health`.
  - Use structural inspection via `codegraph`.

---

## One-Shot MCP tools (`mcp__<server>__<tool>`) Invocations

### 1. Monitor Cognitive Health (`mcp__context_health__get_session_health()`)
Retrieve real-time session health score, token bloat metrics, and read budget status:
```json
{
  "ServerName": "context_health",
  "ToolName": "get_session_health",
  "Arguments": {
    "conversation_id": "<current_conversation_id>"
  }
}
```

### 2. Check File Read Budget (`mcp__context_health__check_read_budget()`)
Verify read quota before reading large or repeatedly inspected files:
```json
{
  "ServerName": "context_health",
  "ToolName": "check_read_budget",
  "Arguments": {
    "file_path": "/path/to/target_file.ts",
    "conversation_id": "<current_conversation_id>"
  }
}
```

### 3. Commit Context Ledger (`mcp__context_health__commit_context_ledger()`)
Checkpoint progress and active constraints to `docs/CONTEXT_LEDGER.md` with deterministic Observation Masking:
```json
{
  "ServerName": "context_health",
  "ToolName": "commit_context_ledger",
  "Arguments": {
    "milestone": "Phase 2 Complete: SOT Grounding and Verification",
    "goals_completed": ["Implemented core calculation adapter", "Added unit tests"],
    "files_modified": ["src/adapter.ts", "src/adapter.test.ts"],
    "active_constraints": ["Zero symlinks invariant", "LineHeight >= 1.45x floor"],
    "project_dir": "/path/to/project"
  }
}
```

### 4. Compact Observations (`mcp__context_health__compact_observations()`)
Compress historical observation logs using deterministic Observation Masking when token pressure rises:
```json
{
  "ServerName": "context_health",
  "ToolName": "compact_observations",
  "Arguments": {
    "conversation_id": "<current_conversation_id>",
    "raw_observations": ["<raw_tool_output_1>", "<raw_tool_output_2>"]
  }
}
```

### 5. Distill Observation Buffer (`mcp__context_health__distill_observation_buffer()`)
Distill `~/.cache/antigravity_observations/<conversation_id>.jsonl` into compact verified facts and sticky decisions:
```json
{
  "ServerName": "context_health",
  "ToolName": "distill_observation_buffer",
  "Arguments": {
    "conversation_id": "<current_conversation_id>"
  }
}
```

### 6. Spillover Large Payload (`mcp__context_health__spillover_large_payload()`)
Offload oversized tool payloads to disk and return a compact summary handle:
```json
{
  "ServerName": "context_health",
  "ToolName": "spillover_large_payload",
  "Arguments": {
    "conversation_id": "<current_conversation_id>",
    "label": "test_suite_stdout",
    "payload": "<large_raw_payload>"
  }
}
```

### 7. Structural Outline (`mcp__codegraph__summarize_path()`)
Inspect classes, functions, and line count metrics without loading raw file bytes into context:
```json
{
  "ServerName": "codegraph",
  "ToolName": "summarize_path",
  "Arguments": {
    "path": "/path/to/source_file.ts"
  }
}
```

### 8. Symbol Diff Extraction (`mcp__codegraph__changed_symbols()`)
Extract modified symbol names from diffs without full file comparisons:
```json
{
  "ServerName": "codegraph",
  "ToolName": "changed_symbols",
  "Arguments": {
    "diff_text": "<git_diff_output>"
  }
}
```

### 9. AST Symbol & Call Graph Alternatives (`codegraph`)
Query definitions, callers, and blast radius in <15ms instead of raw re-reading:
```json
{
  "ServerName": "codegraph",
  "ToolName": "symbol_lookup",
  "Arguments": {
    "root": "/path/to/project",
    "query": "<symbol_name>",
    "limit": 20
  }
}
```
```json
{
  "ServerName": "codegraph",
  "ToolName": "callers_callees",
  "Arguments": {
    "root": "/path/to/project",
    "symbol": "<symbol_name>",
    "limit": 40
  }
}
```

---

## Headroom Fatal-Preserving Compression & Graphify Edge Provenance

### 1. Headroom Fatal-Preserving Log/JSON Compression (`headroomlabs-ai/headroom`)
When tool outputs or test logs exceed `max_chars`, `context_health:spillover_large_payload` (via `compress_fatal_preserving(payload, max_chars=2000)`) applies deterministic middle-out compression:
- **Byte-for-Byte Fatal Preservation**: Every line matching `FATAL|ERROR|CRITICAL|Exception|Traceback|FAIL:` is extracted into `fatal_lines_preserved` and retained **byte-for-byte** inside `compressed_preview` in its original order.
- **Middle-Out Repetitive Collapse**: Repetitive intermediate log/JSON lines between head/tail anchors and fatal lines are collapsed into `... [headroom compressed N repetitive lines] ...`, achieving 60–95% token reduction without losing buried failure root causes.
- **Rule**: Always inspect `compressed_preview` and `fatal_lines_preserved` from `spillover_large_payload` before reading the raw `spillover_path` file on disk.

### 2. Graphify Explicit Edge Provenance (`Graphify-Labs/graphify`)
All structural and knowledge graph tools (`codegraph:callers_callees`, `codegraph:impact_analysis`, `codex_knowledge:graph_query`, `codex_knowledge:graph_neighbors`) tag returned edges and affected files with `edge_provenance_model: "graphify-v1"` and per-edge `provenance`:
- **`provenance: "EXTRACTED"`**: Deterministic AST def-ref symbol edges, explicit imports, or direct 0/1-hop structural relations verified in source/graph tables. Safe to treat as verified ground truth.
- **`provenance: "INFERRED"`**: Heuristic path-stem test matches (`test_stem_match`), module/file-level fallback callees, or multi-hop (`hop >= 2`) associative expansions. Always confirm `INFERRED` edges with a targeted `symbol_lookup` or `extract_symbols` call before mutating code.

---

## Anti-Rot Protocol
1. Check cognitive health via `mcp__context_health__get_session_health()` when entering major phase gates.
2. If read budget warns of exhaustion, switch immediately to `mcp__codegraph__summarize_path()` and `mcp__codegraph__symbol_lookup()`.
3. Commit intermediate milestones via `mcp__context_health__commit_context_ledger()`, compact raw logs via `compact_observations` / `spillover_large_payload`, and distill session memory via `distill_observation_buffer` to maintain deterministic state without re-scanning conversation history.
