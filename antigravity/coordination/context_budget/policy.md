# Context Budget Policy

## Purpose
Manage token and context window usage across agent interactions to prevent overflow and ensure efficient context utilization.

## 3-Tier Adaptive Routing Budgets

### Default Budgets (by Routing Path)
```text
┌───────────────────────────────┬────────────────────────────┬────────────┬───────────┬───────────┐
│ Routing Path                  │ Scope                      │ Max Tokens │ Max Turns │ Max Tools │
├───────────────────────────────┼────────────────────────────┼────────────┼───────────┼───────────┤
│ Path 1: Quick Route           │ <= 3 files, 1 domain       │ 8,000      │ 5         │ 10        │
│ Path 2: Normal Route          │ 4–10 files or 2 domains    │ 25,000     │ 15        │ 30        │
│ Path 3: Long-Horizon Route    │ > 10 files, >= 3 domains   │ 60,000     │ 30        │ 60        │
└───────────────────────────────┴────────────────────────────┴────────────┴───────────┴───────────┘
```

### Budget Categories
1. **Retrieval Budget**: 30% - for `codex_knowledge`, graph, and memory queries
2. **Reasoning Budget**: 40% - for planning, architecture verification (`codex_knowledge` & `codegraph`), and contract consistency checks
3. **Output Budget**: 30% - for code generation, documentation, reviews

## Monitoring
- Use `context-rot-prevention` skill and `call_mcp_tool(ServerName="context_health", ToolName="get_session_health")` / `call_mcp_tool(ServerName="context_health", ToolName="check_read_budget")` to check budget usage
- Use `call_mcp_tool(ServerName="context_health", ToolName="spillover_large_payload")` to offload oversized tool outputs (>8KB) to disk artifacts
- Use `call_mcp_tool(ServerName="codex_knowledge", ToolName="project_context")` for efficient context retrieval (avoids broad scanning)

## Overflow Protocol
1. If context reaches 65%–80% of budget, trigger observation distillation & compaction via `call_mcp_tool(ServerName="context_health", ToolName="distill_observation_buffer")`, `compact_observations`, `commit_context_ledger`, or `/compact`
2. If context exceeds 95% of budget, force checkpoint and restart
3. Use `call_mcp_tool(ServerName="codex_knowledge", ToolName="handoff_checkpoint")` to preserve state across compaction (mandatory at 60% budget on Path 3)

## Integration with 8-Stage Pipeline
Each stage in the 8-Stage Pipeline gets a proportional budget slice:
- **Stage 1 (Intake) & Stage 2 (Enrichment)**: 10% of total budget
- **Stage 3 (Clarification) & Stage 4 (PM Contract & Story Shards)**: 15% of total budget
- **Stage 5 (Disjoint Specialist Builders) & Stage 6 (Surgical Implementation)**: 50% of total budget
- **Stage 7 (Two-Stage QC: 7a Static + 7b Dynamic)**: 10% of total budget
- **Stage 8 (Independent Oracle Audit)**: 15% of total budget

## Cache Budget Allocation

Of the total context budget, allocate for cacheability:

```text
┌─────────────────────────────────────────────┬─────────────┬────────────┬───────────────────────────────┐
│ Category                                    │ % of Budget │ Cacheable? │ Notes                         │
├─────────────────────────────────────────────┼─────────────┼────────────┼───────────────────────────────┤
│ System prefix (rules, tools, identity)      │ 40%         │ Yes        │ Stable across sessions        │
│ Task context (contract, files, trajectory)  │ 30%         │ No         │ Dynamic per task              │
│ Tool results and output                     │ 30%         │ Partial    │ Reusable via semantic cache   │
└─────────────────────────────────────────────┴─────────────┴────────────┴───────────────────────────────┘
```

### Cache Hit Rate Targets
- Provider-side prefix cache: ≥ 80% hit rate (system prompt + tools)
- Semantic cache (SQLite vector/FTS): ≥ 60% hit rate for similar queries
- Plan cache (architectural patterns via `codex_knowledge` & `codegraph`): ≥ 40% hit rate for recurring goal patterns

### Cache Boundary Protocol
At each pipeline stage transition, emit a cache boundary marker:
```yaml
cache_boundary:
  stage: <stage_name>
  prefix_stable: true
  dynamic_content_start: true
  budget_used: <tokens>
  budget_remaining: <tokens>
```

### Cache Invalidation Rules
1. When a file is modified, invalidate semantic cache entries referencing that file
2. When an architectural plan or pattern is updated in `codex_knowledge`, invalidate the old plan cache entry
3. When the system prefix is updated (new cache_version), all provider-side caches are invalidated
4. Semantic cache entries expire after TTL (default: 3600 seconds)
