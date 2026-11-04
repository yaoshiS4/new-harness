---
description: Context-budget health check and compaction protocol - measures usage, applies efficient retrieval, and decides continue / compact / checkpoint-and-restart. Run before Oracle, every ~5 tool calls on long tasks, or when context feels heavy.
---

# /token-check

1. Measure: read the status line context gauge (55% DEGRADED, 65% compact, 75% CRITICAL, 95% hard stop) and `mcp__context_health__get_session_health(conversation_id="${CLAUDE_SESSION_ID}")`.
2. Retrieval discipline from here on: `mcp__codex_knowledge__project_context` / `memory_query` / `graph_query` before broad reads; `mcp__codegraph__extract_symbols` instead of sequential slices; `mcp__context_health__check_read_budget` before re-reading a file; payloads > 8 KB go through `mcp__context_health__spillover_large_payload`.
3. Act on pressure:
   - 65-80%: `mcp__context_health__distill_observation_buffer`, `compact_observations`, `commit_context_ledger(milestone, goals_completed, files_modified, active_constraints, project_dir)` (or `mcp__codex_knowledge__handoff_checkpoint`), then `/compact`. Delegate the remaining heavy multi-file work to subagents.
   - >= 95%: hard stop; checkpoint; offer a fresh session with the handoff name.
4. Report:
```yaml
token_check:
  percent_used: <n>
  action: continue | compact | checkpoint_and_restart
  checkpoint_ref: "<name or none>"
  retrieval_optimizations: []
```
