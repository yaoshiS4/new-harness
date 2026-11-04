---
name: spawn-governance
description: Govern subagent spawning with explicit scope, file ownership, and output requirements. Validate before spawning.
---

# Spawn Governance

## Purpose
Prevent uncontrolled agent spawning and scope bleed by requiring explicit Story Shard leases, Harmony CP-1 factorized authority tags, model routing compliance, and a 2-stage post-return review gate before accepting subagent work.

---

## Rules

### 1. Validate Before Spawning (Model Routing & Helper Sizing)
Before invoking any subagent via `invoke_subagent`, verify:
- **Task & Acceptance Clarity**: The prompt defines exact target coordinates, output format, and verification command.
- **Gemini-Only Model Routing Compliance**:
  - Read-Only Explorers (`Role: "backend-explorer" | "frontend-explorer" | "research-explorer" | "test-runner" | "doc-sync-worker"`): Use `TypeName: "research"`, `Model: "flash"` (or `Model: "flash_lite"` for diff/telemetry helpers).
  - Write-Capable Builders, Architects & Auditors (`Role: "dev-fe" | "dev-be" | "debugger" | "sa" | "oracle-review"`): Use `TypeName: "self"`, `Model: "inherit"` (`gemini-4-argon-medium`).
  - **Escalation Gate**: Escalating any subagent to `Model: "pro"` (`gemini-4-argon-high`) is forbidden unless explicitly approved by the user via `ask_question` (`force_ask`).
- **Non-Overlapping File Leases**: `allowed_files` are disjoint across all active concurrent Builders.

### 2. Define Spawn Contract & Harmony CP-1 Factorized Lease Tags
Every Builder/Explorer spawn contract must declare its **Harmony Harness CP-1 Factorized Lease** ($\mathcal{H}_{\text{gen}} \oplus \mathcal{H}_{\text{env}}$):
- `H_gen` (Generator Lease): Grants write access strictly to `allowed_files` within the Story Shard. Zero authority to mutate verification harnesses, test assertions (`Fix-The-Code-Not-The-Test`), or hook guardrails.
- `H_env` (Environment / Evaluator Lease): Reserved for QC, test-runner, and `oracle-review` agents to execute verification suites and inspect diffs read-only.

```yaml
spawn_contract:
  agent_role: <dev-fe | dev-be | debugger | backend-explorer | oracle-review>
  type_name: <self | research>
  model: <inherit | flash | flash_lite>
  cp1_lease_partition: <H_gen | H_env>
  oracle_custody_lease: <Oracle-Custody-Lease-ID>
  task: <clear task description>
  allowed_files:
    - <explicit file path>
  required_tests: <exact verification command>
  scope_drift_budget: 5%
  workspace_mode: <inherit | share | branch>
```

### 3. File Ownership & Concurrency Bounds
- Only one write-capable Builder (`H_gen`) may own a file set at a time.
- Use `worktree-isolation` (`Workspace: "share"` or `"branch"`, or `git worktree add`) when running parallel write waves.
- Create lock files in `.agent-locks/` for file ownership (expire after 30 minutes).
- Maximum 2 write-capable agents active simultaneously; maximum 3 agents per wave.

### 4. Output Requirements (Summary-Only Return & Reactive Wakeup)
- Never poll subagents in a loop; yield turn immediately after `invoke_subagent` for reactive wakeup.
- No sibling-to-sibling messaging; all communication routes strictly through the parent orchestrator/PM.
- Subagent returns must be compact and include the mandatory `### Telemetry Receipt` footer.

### 5. Two-Stage Subagent Review Protocol (`obra/superpowers` — `subagent-driven-development`)
Never trust a Builder's self-reported success without executing the sequential 2-stage verification gate:

#### Stage A: Spec & Scope Lease Compliance Check (Mechanical Gate)
1. Verify that **only** files listed in `allowed_files` were touched (`git diff --name-only` and `stop_hook.py` `_check_subagent_scope_drift`).
2. Confirm every requirement in the Story Shard was implemented with zero unrequested features (`codegraph:changed_symbols`).
3. Verify the `### Telemetry Receipt` contains a fresh `exit_code: 0` from `required_tests`.
   - *If Stage A fails*: Reject and route `Fail: <path:line>` back to the Builder before inspecting code style.

#### Stage B: Code Quality & Anti-Slop Audit (Evaluator Gate)
1. Only after Stage A passes, inspect the diff for surgical minimalism (`~/.gemini/antigravity/scripts/clean-diff.sh`), security invariants, and zero weakened test assertions.
2. If UI files (`*.tsx`, `*.css`, `*.vue`, `*.kt`) were touched, enforce the mandatory `frontend-qc` Anti-Slop Pass (zero nested cards `L-01`, card soup `L-13`, badge proliferation `D-09`, or ellipsis clipping `L-16`).

### 6. Subagent Telemetry Receipt Contract (MAST Defense)
Every Builder and Explorer subagent return message via `send_message` MUST conclude with a machine-parseable `### Telemetry Receipt` footer block to prevent Information Withholding:
```yaml
### Telemetry Receipt
cp1_lease: <H_gen | H_env>
files_touched:
  - <path1>
verified_symbols:
  - <symbol1>
verification_cmd: "<command executed>"
exit_code: 0
stage_a_spec_compliance: pass
stage_b_quality_gate: pass
residual_risks: "<none | specific risk>"
```

### 7. `s10_team_protocols` Lease Ack & Idempotent Handoff Contract (`shareAI-lab/learn-claude-code`)
To prevent ghost dispatches, duplicate mutations, or ambiguous subagent ownership across multi-agent waves:
1. **Turn-1 Subagent Lease Validation (`s10` Ack)**:
   - On Turn 1, the spawned subagent MUST validate that every target file in `allowed_files` exists (or its parent directory exists for explicitly declared new files) and confirm its `cp1_lease_partition` (`H_gen` vs `H_env`) before executing any write or command tool.
   - If a leased path is missing, locked by another active agent, or violates the CP-1 partition, the subagent immediately aborts and returns `status: rejected_lease` to the parent without mutating workspace state.
2. **Parent Immutable Lease State Transitions**:
   - The parent orchestrator (`pm`) records immutable `lease_id -> conversation_id -> status` transitions (`ISSUED -> ACKED -> COMPLETED | FAILED | REVOKED`) in the active wave ledger (`codex_knowledge:handoff_checkpoint`).
   - Re-dispatching a failed or timed-out shard requires revoking the prior `lease_id` and issuing a fresh idempotent handoff envelope so late messages from stale subagent conversations cannot overwrite verified work.

## Output Format
```yaml
spawn_result:
  agent_role: <role>
  model: <inherit|flash|flash_lite>
  cp1_lease: <H_gen|H_env>
  status: <completed|failed|timed_out>
  stage_a_spec_lease: <pass|fail>
  stage_b_code_quality: <pass|fail>
  changed_files: <list>
  evidence: <verification command output>
  risks: <list of identified risks>
  next_action: <recommended next step>
```
