# Full protocol: context-rot-prevention

Loaded on demand; see SKILL.md for triggers and core rules.

## 1. Cadence & Telemetry

Evaluate context saturation at:
1. **SOL Phase Boundaries**: Scope Lock, Plan Review, Pre-Implementation, and Post-Validation.
2. **Periodic Interval**: Every 10 continuous turns in long-running tasks.
3. **Loop Warnings**: Immediately upon encountering repeated tool errors or repeated file queries.

### Status Directives

| Turn / Saturation | Status | Directive | Action Required |
|---|---|---|---|
| **< 10 turns** | `HEALTHY` | `PROCEED` | Continue normal execution within standard token budget. |
| **10 – 20 turns** | `DEGRADED` | `COMPACT_LEDGER` | Context pressure reached (~80% budget). Summarize progress in `task.md` and prune active context. |
| **> 20 turns** | `CRITICAL` | `MANDATE_ISOLATION` | Severe context rot risk. Stop inline exploration. Checkpoint state and delegate subtasks via spawn governance. |

## 2. Subagent Isolation Trigger

When `status == CRITICAL`, `step_count > 30`, or when a subtask is projected to require >10 steps or span >2 files:
- **Never explore inline**. Inline multi-file exploration in degraded sessions causes rapid reasoning collapse.
- **Dispatch via Spawn Governance (the `Agent` tool)**:
  - For read-only exploration: `Agent(subagent_type="backend-explorer" | "frontend-explorer", model="sonnet", Prompt="...")`.
  - For scoped implementation: `Agent(subagent_type="dev-be" | "dev-fe", model="inherit", Prompt="...")` with an explicit `allowed_files` Story Shard lease.
- **Contract Boundary**: Enforce strict return contracts: subagents return only compact summaries and verified diffs, never raw transcript logs.

## 3. Mid-Session Checkpoints

Mid-session checkpoints protect against context loss before session end:
- Invoke `context_health:commit_context_ledger`, `context_health:distill_observation_buffer`, and `codex_knowledge:handoff_checkpoint(slug, name, payload)` via MCP tools (`mcp__<server>__<tool>`):
  - At `DEGRADED` state (~60–80% budget).
  - At major architectural milestones (e.g. completing a sub-module).
- Appends structured records to `task.md` and `docs/CONTEXT_LEDGER.md`.
- At session completion, archive the distilled observation buffer (`distill_observation_buffer`) and final state into `codex_knowledge:handoff_checkpoint(slug, name, payload)`.

## 4. Constraint Pinning (Tier C Recency Attention)

Academic research proves attention follows a U-shaped curve: models attend strongest to the prompt beginning and the prompt tail (recency).

- **Strict Cache Rule**: NEVER modify `templates/system_prefix.md`. The system prefix must remain byte-identical across all turns to preserve prompt cache.
- **Recency Pinning**: In sessions with >20 turns or when health is `DEGRADED`, pin critical constraints as a compact block (≤5 lines) at the tail of the current user-turn message:
  ```markdown
  [INVARIANT CHECK: Health Score: <score> | Active Read Limit: 3-strikes | Lock: <holder> | Contract Scope: <scope>]
  ```
