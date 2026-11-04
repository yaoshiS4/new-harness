---
name: spawn-governance
description: Govern subagent spawning with explicit scope, file ownership, and output requirements. Validate before spawning.
---

# Spawn Governance (Claude Code)

## Purpose
Prevent uncontrolled agent spawning and scope bleed by requiring explicit Story Shard leases, Harmony CP-1 factorized authority tags, model-routing compliance, and a two-stage post-return review gate before accepting subagent work. Enforcement: the PreToolUse hook denies builder dispatches without `allowed_files:`, prompts over 6,000 chars, nested spawning, and model escalation without confirmation; the SubagentStop hook records scope drift.

---

## Rules

### 1. Validate before spawning (routing and sizing)
Before every `Agent` call verify:
- **Task and acceptance clarity**: the prompt defines exact target coordinates (`path:line`), the output format, and the `verification_cmd`.
- **Model routing**: read-only roles (`backend-explorer`, `frontend-explorer`, `research-explorer`, `test-runner`, `doc-sync-worker`, `librarian`, `user-tester`, `devops`) run on `sonnet`; `diff-helper` on `haiku`; builders, architects, QC, and auditors (`dev-fe`, `dev-be`, `debugger`, `designer`, `sa`, `critical-planner`, `frontend-qc`, `oracle-review`, `hallucination-auditor`, `security-audit`) on `inherit`. These are the agents' frontmatter defaults; do not pass `model:` unless downgrading.
- **Escalation gate**: `model: opus` or `fable` for a role above its baseline requires explicit user approval (AskUserQuestion); the hook converts it into a permission prompt.
- **Non-overlapping file leases**: `allowed_files` are disjoint across all concurrently active builders.

### 2. Spawn contract and Harmony CP-1 factorized lease tags
Every builder or explorer prompt declares its CP-1 lease (H_gen ⊕ H_env):
- `H_gen` (generator lease): write access strictly to `allowed_files` inside the Story Shard; zero authority over verification harnesses, test assertions (Fix-The-Code-Not-The-Test), or hook guardrails.
- `H_env` (environment / evaluator lease): QC, `test-runner`, and `oracle-review` execute verification suites and inspect diffs read-only.

```yaml
spawn_contract:
  subagent_type: <dev-fe | dev-be | debugger | designer | backend-explorer | frontend-explorer | research-explorer | test-runner | frontend-qc | oracle-review>
  model: <inherit | sonnet | haiku>        # frontmatter default unless downgrading
  cp1_lease_partition: <H_gen | H_env>
  oracle_custody_lease: <NONE | UPDATE_ASSERTIONS>
  task: <clear task description with path:line coordinates>
  allowed_files:
    - <explicit file path or glob>
  required_tests: <exact verification command>
  scope_drift_budget: 5%
  isolation: <none | worktree>              # Agent tool `isolation: "worktree"` for parallel write waves
```
The prompt body starts with `Role: <subagent_type>` followed by the contract verbatim, then the brief. Keep it under 6,000 chars; long specs go to a scratch file passed by path.

### 3. File ownership and concurrency bounds
- One write-capable builder (`H_gen`) owns a file set at a time.
- Parallel write waves use `isolation: "worktree"` on the Agent call (or `git worktree add`) per the `worktree-isolation` skill; never two builders in the same working tree.
- Record ownership in `task.md` (shard -> agent -> state); lease entries expire with the wave (30 minutes default).
- Maximum 2 write-capable agents active simultaneously; maximum 4 agents per wave; subagents never spawn subagents.

### 4. Output requirements (summary-only return, reactive wakeup)
- Never poll: after dispatch, yield the turn and act on the completion notification. Background agents report back automatically.
- No sibling-to-sibling coordination; everything routes through the orchestrator.
- Returns are compact (changed files, evidence, risks, next action) and end with the mandatory `### Telemetry Receipt` footer.

### 5. Two-stage subagent review protocol
Never trust a builder's self-reported success without the sequential gate:

**Stage A: spec and lease compliance (mechanical)**
1. Only `allowed_files` were touched (`git diff --name-only`; the SubagentStop hook also records drift).
2. Every shard requirement is implemented with zero unrequested features (`mcp__codegraph__changed_symbols`).
3. The `### Telemetry Receipt` contains a fresh `exit_code: 0` from `required_tests`.
If Stage A fails: reject with `Fail: <path:line> | Expected | Got | Cause | Fix` and route back to the builder before looking at style.

**Stage B: code quality and anti-slop (evaluator)**
1. Inspect the diff for surgical minimalism (`bash ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/clean-diff.sh`), security invariants, and zero weakened assertions.
2. If UI files (`*.tsx`, `*.css`, `*.vue`, `*.kt`) changed, run the mandatory `frontend-qc` anti-slop pass (L-01 nested cards, L-13 card soup, D-09 badge proliferation, L-16 ellipsis clipping).

### 6. Telemetry receipt contract (MAST defense against information withholding)
Every builder and explorer return ends with:
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

### 7. Lease acknowledgement and idempotent handoff
1. **Turn-1 lease validation**: the spawned subagent confirms that every path in `allowed_files` exists (or its parent directory exists for declared new files) and states its `cp1_lease_partition` before any write or command. A missing, locked, or partition-violating path -> abort with `status: rejected_lease` and no workspace mutation.
2. **Immutable lease transitions**: the orchestrator records `shard_id -> agent -> ISSUED | ACKED | COMPLETED | FAILED | REVOKED` in `task.md` (and `mcp__codex_knowledge__handoff_checkpoint` on Path 3). Re-dispatching a failed or timed-out shard requires revoking the prior lease and issuing a fresh envelope so stale results cannot overwrite verified work.

## Output format
```yaml
spawn_result:
  subagent_type: <role>
  model: <inherit | sonnet | haiku>
  cp1_lease: <H_gen | H_env>
  status: <completed | failed | timed_out | rejected_lease>
  stage_a_spec_lease: <pass | fail>
  stage_b_code_quality: <pass | fail>
  changed_files: <list>
  evidence: <verification command output>
  risks: <list>
  next_action: <recommended next step>
```
