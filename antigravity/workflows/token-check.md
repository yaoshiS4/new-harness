---
name: token-check
summary: Measure context load, use efficient retrieval, and checkpoint when context pressure rises.
---

# Token Check

## Purpose
Monitor and manage context window usage to prevent overflow and degraded reasoning.

## When to Run
- Before starting any task (baseline measurement)
- After every 5 tool calls (progressive monitoring)
- When context feels heavy (subjective check)
- Before Oracle review (pre-review check)

## Steps

### 1. Measure Context Load
- Estimate current context usage
- Compare against allocated budget per `../coordination/context_budget/policy.md`
- Calculate percentage used

### 2. Use Efficient Retrieval
- Replace broad file reads with targeted queries:
  - Use `call_mcp_tool` on `codex_knowledge` (`project_context`) instead of reading entire docs
  - Use `call_mcp_tool` on `codex_knowledge` (`memory_query`) instead of re-reading conversation history
  - Use `call_mcp_tool` on `codex_knowledge` (`graph_query`) instead of searching all files
  - Use `call_mcp_tool` on `context_health` (`get_session_health` / `check_read_budget`) to inspect session health
  - Use `call_mcp_tool` on `context_health` (`spillover_large_payload`) to offload large tool outputs (>8KB) to disk artifacts with compact summary handles

### 3. Checkpoint When Pressure Rises
- At 65%–80% budget: trigger observation distillation & compaction
  - Run `call_mcp_tool` on `context_health` (`distill_observation_buffer` and `compact_observations`) to compress raw tool telemetry into high-signal semantic observations
  - Use `call_mcp_tool` on `codex_knowledge` (`handoff_checkpoint`) or `context_health` (`commit_context_ledger`) to save state
  - Summarize key context into memory
  - Suggest `/compact` or delegate remaining multi-file work to subagents
- At 95% budget: hard stop
  - Checkpoint immediately
  - Offer a fresh session from checkpoint
  - Do NOT attempt to continue inline with degraded context

### 4. Report Context Status
```yaml
token_check:
  budget_allocated: <tokens>
  budget_used: <tokens>
  percent_used: <percentage>
  action: <continue|compact|checkpoint_and_restart>
  checkpoint_ref: <name if saved>
  retrieval_optimizations: <list of efficient retrievals used>
```
