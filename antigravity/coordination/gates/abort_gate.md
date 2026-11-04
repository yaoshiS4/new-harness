# Abort Gate

## Purpose
Stop execution when continuing would increase risk or waste resources. Abort is a controlled, reversible halt—not a panic exit. Checkpoint state before aborting so work can be resumed.

## Abort Decision Tree

```
PM or agent detects a critical issue
    │
    ▼
Is the issue recoverable within the current task contract?
    │
    ├── YES → Attempt recovery (see skills/loop-detection/SKILL.md)
    │           └── Recovery successful? → Resume execution
    │           └── Recovery failed? → Proceed to abort assessment
    │
    └── NO → Proceed to abort assessment
                │
                ▼
        Is there a simpler alternative scope that still delivers value?
            │
            ├── YES → Attempt reframe (reduce scope, decompose task)
            │           └── Reframe accepted? → Resume with new contract
            │           └── Reframe rejected? → Proceed to abort
            │
            └── NO → Proceed to abort
                        │
                        ▼
                Checkpoint state (Section 2)
                        │
                        ▼
                Produce abort artifact (Section 4)
                        │
                        ▼
                Notify user/PM of recovery options (Section 5)
```

## When to Trigger

Trigger the abort gate when ANY of the following conditions are met:

| Condition | Detection Method | Severity |
|-----------|------------------|----------|
| Context budget exhausted (>95% used) | `skills/context-rot-prevention/SKILL.md` | Critical |
| Critical AOP conflict that cannot be resolved | `call_mcp_tool(ServerName="codex_knowledge", ToolName="graph_query")` returns critical conflicts after 2 resolution attempts | Critical |
| Scope drift exceeds budget with no path to recovery | `skills/scope-drift-control/SKILL.md` shows >5% drift AND PM cannot absorb the drift | Critical |
| User explicitly cancels | User message | Critical |
| Unrecoverable environment error | Command executed via `run_command` fails with infrastructure error (disk full, network down, missing system dependency) | Critical |
| Security breach or secret leak | `rg` / `skills/security-audit/SKILL.md` finds committed secrets or unauthorized access pattern | Critical |
| Agent stuck in infinite loop | Same file edited >3 times with no test improvement | Major |

**Do NOT trigger abort for:**
- Minor test failures (use revision_gate instead)
- LSP warnings in untouched files (out of scope)
- Single failed tool invocation (retry first)
- Disagreement between builder and Oracle on style (escalate instead)

---

## Steps

### 1. Assess the Situation

Before aborting, PM MUST answer these questions:

| Question | How to Answer | Tool |
|----------|-------------|------|
| Why is continuation risky or wasteful? | Document the specific condition from the trigger table above | Manual assessment |
| Is there a simpler alternative? | Check if the task can be decomposed into a smaller scope that still meets core acceptance criteria | `skills/routing-thresholds/SKILL.md` with reduced `file_count` |
| Can the task be decomposed? | Identify the minimal subset of acceptance criteria that are still achievable | PM task contract review with revised scope |
| What is the cost of aborting vs. continuing? | Estimate tokens/time saved by aborting vs. potential value of partial completion | Manual assessment |

**Decision Rule:**
- If a simpler alternative exists AND it can be validated within 10% of remaining context budget → **Reframe** (see `skills/loop-detection/SKILL.md`).
- If no simpler alternative exists OR reframe failed → **Proceed to abort**.

---

### 2. Checkpoint State

Before aborting, ALWAYS preserve state:

1. **Create Handoff Checkpoint:**
   ```yaml
   # Use call_mcp_tool (ServerName: "codex_knowledge", ToolName: "handoff_checkpoint")
   name: "abort_<task_ref>_<timestamp>"
   payload: |
     task_ref: <task contract ID>
     abort_reason: <specific condition>
     accomplished: <list of completed slices/acceptance criteria>
     remaining: <list of uncompleted slices/acceptance criteria>
     open_branches: <list of git branches>
     open_files: <list of files with uncommitted changes>
     last_oracle_verdict: <PASS|CONDITIONAL|FAIL or "none">
     context_used: <token count>
     context_remaining: <token count>
   ```

2. **Save Intermediate Results:**
   - Use `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "knowledge_capture"`) to save:
     - `key`: `abort_intermediate_<task_ref>`
     - `value`: JSON with all intermediate artifacts (proposals, merge results, test outputs)
   - Use `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "handoff_checkpoint"`) to create an audit trail:
     - `trace_class`: "abort_checkpoint"
     - `title`: "Abort checkpoint for <task_ref>"
     - `payload`: { `checkpoint_ref`, `reason`, `accomplished`, `remaining` }

3. **Preserve Git State:**
   - If uncommitted changes exist, builder creates a WIP commit:
     ```bash
     git add -A && git commit -m "WIP: abort checkpoint for <task_ref>"
     ```
   - Tag the commit: `git tag abort-<task_ref>-<timestamp>`

---

### 3. Decide: Abort or Reframe

**Reframe Attempt (if applicable):**
- Reduce the task scope to the minimum viable subset.
- Update the task contract with PM task contract review.
- Re-run `preflight_gate` to validate the reframed task.
- If preflight passes, resume execution with the new contract.
- If preflight fails, proceed to abort.

**Abort Decision:**
- If reframing is not possible or has failed, proceed with abort.
- Document the final decision and rationale.

---

### 4. Abort

1. **Record Abort Reason:**
   - Use `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "knowledge_capture"`):
     - `key`: `abort_reason_<task_ref>`
     - `value`: detailed explanation of why execution was halted
   - Use `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "handoff_checkpoint"`):
     - `trace_class`: "abort"
     - `title`: "Execution aborted: <task_ref>"
     - `payload`: { `reason`, `checkpoint_ref`, `accomplished`, `remaining` }

2. **Produce Abort Summary:**
   Return the following YAML artifact to the caller:

   ```yaml
   abort:
     abort_id: <unique identifier>
     task_ref: <task contract ID>
     timestamp: <ISO-8601>
     reason: <specific condition from trigger table>
     reason_detail: <detailed explanation>

     checkpoint_ref: <handoff checkpoint name>
     git_tag: <tag name or "none">

     accomplished:
       - item: <what was completed>
         evidence: <test results, merge artifacts, etc.>
     remaining:
       - item: <what remains>
         blocker: <why it could not be completed>

     context_used: <token count>
     context_remaining: <token count>

     reframe_attempted: <true|false>
     reframe_result: <success|failed|not_attempted>

     recommendation: <what to do next>
     resumable: <true|false>
   ```

3. **Clean Up (Optional):**
   - Close temporary branches if they will not be resumed.
   - Release lock files in `.agent-locks/`.
   - Do NOT delete the checkpoint or git tag.

---

### 5. Recovery

The abort gate provides three recovery paths:

| Recovery Path | Condition | Action |
|---------------|-----------|--------|
| **Resume from Checkpoint** | `resumable: true` and user wants to continue | PM loads checkpoint via `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "checkpoint_restore"`); builder resumes from saved state |
| **Re-scope and Restart** | Task was too large or poorly defined | PM creates a new, smaller task contract; begins fresh pipeline |
| **Try Different Approach** | Current approach was fundamentally flawed | PM selects alternative approach from proposals or spawns new exploration |

**Recovery Steps:**
1. User or PM decides which recovery path to take.
2. If resuming:
   - Restore checkpoint: `call_mcp_tool(ServerName="codex_knowledge", ToolName="checkpoint_restore")` with `name` from `checkpoint_ref`.
   - Checkout git tag: `run_command` with `git checkout <git_tag>`.
   - Re-run `preflight_gate` to validate readiness.
3. If re-scoping:
   - Draft new task contract.
   - Run PM task contract review.
   - Begin new pipeline.
4. If trying different approach:
   - Load alternative proposals via `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "handoff_read"`).
   - Select new approach.
   - Update task contract and restart.

---

## Guardrails

| Guardrail | Enforcement | Violation Action |
|-----------|-------------|------------------|
| Always checkpoint before abort | PM verifies `checkpoint_ref` exists before declaring abort complete | Delay abort until checkpoint is confirmed |
| Do not delete WIP branches without user consent | Branches tagged with `abort-<task_ref>-<timestamp>` are preserved | Warn user before any branch deletion |
| Abort reason must be specific | `reason` field must match a condition from the trigger table | Reject vague abort summaries |
| Reframe must be attempted once | PM must document reframe attempt in `reframe_attempted` | If false, require justification |
| Recovery options must be presented | Abort artifact must include at least 2 recovery paths | Return abort artifact for revision |

---

## Tool References

| Tool | Purpose | When to Invoke |
|------|---------|----------------|
| `context-rot-prevention` skill | Detect context budget exhaustion | Continuously during execution |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="graph_query")` | Detect critical AOP conflicts | After major architectural changes |
| `scope-drift-control` skill | Measure scope drift | Before and after each slice |
| PM task contract review | Validate scope and reframe attempts | Before abort and during reframe |
| `routing-thresholds` skill | Check if simpler alternative exists | During abort assessment |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="handoff_checkpoint")` | Save state before abort | Mandatory before every abort |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="checkpoint_restore")` | Resume from checkpoint | During recovery |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="knowledge_capture")` | Persist abort metadata | During abort and recovery |
| `rg` | Detect secrets or unauthorized patterns | During security-related aborts |
| `run_command` with `git commit`, `git tag` | Preserve git state | During checkpoint |
