# Full protocol: loop-detection

Loaded on demand; see SKILL.md for triggers and core rules.

### Rule 2A: Provider Loop Fault Rule
If the provider or client returns an error containing `Repetitive tool calls detected` or `InternalError.Algo.InvalidParameter`:
- **STOP tool use immediately**
- Do not retry the same tool name, command, or semantically equivalent retrieval in the same conversation history
- Audit recent tool-call history for duplicate name+argument pairs
- Reframe with a different evidence source, or ask the user to start a fresh thread if the conversation history itself is poisoned
- Treat the provider error object as diagnostic text; do not pass the raw `{"code": ..., "message": ..., "request_id": ...}` object into a content/tool schema that requires a `type` discriminator


---
## Loop Breaking Actions

When a loop is detected, take ONE of these actions in order:

1. **Reframe**: Describe the problem differently and try a completely different tool or approach
2. **Reduce**: Simplify the task to a smaller scope that can be verified
3. **Escalate**: Ask the user for clarification or manual intervention
4. **Checkpoint**: Save state via MCP tools (`mcp__<server>__<tool>`) (`ServerName: "codex_knowledge"`, `ToolName: "handoff_checkpoint"`) and start fresh

## Tool-Call Dedupe Preflight

Before calling a tool after the fifth tool call in a task:
- Compare the planned tool name and serialized arguments with recent calls in the conversation history.
- If an identical call already ran and no file/process/network state changed, skip it and use the existing evidence.
- If a repeat is necessary, vary the arguments meaningfully: line range, file set, query terms, or validation target.
- If you cannot vary the call without losing correctness, stop and report the blocker instead of risking a provider-level loop fault.

## Integration with Antigravity Lifecycle Hooks & Sentinels

- **JEV Stagnation Breaker (`pre_tool_use.py` & `post_tool_use.py`)**: Computes Jaccard-Entropy-Velocity over sliding tool-call windows and mechanically blocks repetitive tool loops or zero-progress error cycles.
- **3-Slice Sequential Read Loop Breaker (`pre_tool_use.py`)**: Blocks `>= 3` sequential `Read` slices on the same file without intermediate edits; forces immediate cutover to `codegraph:extract_symbols(root, path, symbols)` or `codegraph:batch_query(root, steps)`.
- **AdaSearch Directive (`post_tool_use.py`)**: After 2 consecutive zero-hit or repetitive search turns (`rg`/`fd`), injects an adaptive search pivot directive requiring AST symbol lookup (`codegraph:symbol_lookup`) or broader structural summarization (`codegraph:summarize_path`).
- **Burn-Rate Sentinel (`antigravity/scripts/burn-rate-sentinel.py`)**: Monitors token velocity, tool-call frequency, and loop stagnation across active sessions to trigger proactive circuit-breaking before budget exhaustion.
- **Knowledge Persistence (`codex_knowledge:memory_store`, `graph_query`, `orchestration_lesson`)**: Persist resolved loop root causes via `mcp__codex_knowledge__memory_store(, Arguments={"slug": "<slug>", "key": "<loop_signature>", "value": "<remediation>"})`, classify failure patterns via `graph_query`, and record dreaming lessons via `orchestration_lesson`.

## NEVER
- Never retry the same approach more than 3 times
- Never ignore an error that appears 3+ times
- Never add more context when already at 80% budget
- Never continue a task that shows no progress after 5 tool calls
