---
name: loop-detection
description: Active loop detection and breaker for repeating actions, identical errors, or stalled tool cycles.
---

# Loop Detection Skill

## Purpose
Detect and break active loops during agent sessions. ENFORCED mechanism, not just advice.

## Loop Detection Rules

### Rule 1: Three-Strike Rule
If you call the same tool with equivalent arguments **3 times** without progress:
- **Enforcement**: Mechanical PreToolUse hook blocks the 3rd identical call or whole-file re-read.
- **STOP immediately**: Summarize attempt, switch to `rg -n`, `call_mcp_tool(ServerName="codegraph", ToolName="symbol_lookup")`, or `call_mcp_tool(ServerName="codegraph", ToolName="summarize_path")`. If stuck, ask user.

### Rule 2: Error Loop Rule
If you receive the same error message **3 times in a row**:
- **STOP immediately**: Error is environmental; report with context and suggest manual intervention.

### Rule 3: Progress Check
After every **5 tool calls** in a single task:
- Check if measurable progress occurred. If not, reframe and checkpoint via `call_mcp_tool(ServerName="codex_knowledge", ToolName="handoff_checkpoint")` or `task.md`.

### Rule 4: Context Pressure
If context exceeds **80% of budget** or conversation exceeds 20 turns:
- Trigger compaction: summarize established state, prune ephemeral context, and checkpoint progress.
- Mandate subagent isolation for complex subtasks.

### Rule 5: External Web & Social Scraper Terminal Error Codes (`FINAL_CODES`)
When invoking `agent-reach` (`agent_reach.cli`) or `opencli` adapters, inspect the JSON envelope (`{schema_version, ok, channel, action, backend, items, meta, error}` or `{ok, data, error: {code, message, hint}}`).
- **Immediate Single-Strike Trip**: Any terminal error code in `FINAL_CODES = {PLATFORM_BLOCKED, RATE_LIMITED, NEED_LOGIN, BUSY, NOT_FOUND, BAD_INPUT}` trips the circuit breaker on the **first occurrence** (1-strike breaker; never wait for 3 strikes).
- **Mandatory Action**: Stop retrying the target immediately, do **not** rotate accounts, backends, or browser sessions to bypass the block, and synthesize using already-collected public ground truth or fallback to offline/canonical sources.

## Full Protocol
Load `references/protocol.md` before executing beyond the core rules above.
