---
name: scope-drift-control
description: Compare actual output against validated intent. Record drift and stop when the budget is exceeded.
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# Scope Drift Control

## Purpose
Prevent scope creep and unrequested edits by comparing actual file and AST symbol modifications (`codegraph:changed_symbols`) against the leased Story Shard (`allowed_files`), enforcing the Zero Orthogonal Drift Rule, and stopping immediately when the drift budget is exceeded.

> [!IMPORTANT]
> **Zero Orthogonal Drift Rule (`forrestchang/andrej-karpathy-skills` — Surgical Changes)**:
> - **Touch ONLY what the Story Shard requires**: Every changed line must trace directly to the user's request or the leased Story Shard.
> - **Zero Drive-By Refactors**: Do not reformat adjacent code, rename untouched variables, reorganize imports, or "improve" unrelated functions in leased files.
> - **Remove Only Your Own Orphans**: Clean up imports or helpers that *your own changes* made unused, but never delete pre-existing dead code outside your task scope unless explicitly requested.

---

## Drift Budget
- **File Lease Budget**: `0` unleased files (strictly enforced by `stop.py` `_check_subagent_scope_drift` against `allowed_files`).
- **Feature / Symbol Drift Budget**: Default `<= 5%` of original planned scope; zero orthogonal symbol mutations inside leased files.

---

## Steps

### 1. Establish Scope & Symbol Baseline
At task start, record the leased Story Shard baseline:
```yaml
scope_baseline:
  oracle_custody_lease: "<OCL-id>"
  allowed_files:
    - "<explicit leased file paths>"
  planned_symbols:
    - "<target functions/classes to add or modify>"
  planned_tests:
    - "<target test cases>"
  drift_budget_percent: 5
```

### 2. Monitor File Leases & AST Symbol Drift (`codegraph:changed_symbols`)
After each implementation step, verify both file-level and AST symbol-level boundaries:
1. **File Lease Check (`allowed_files`)**:
   Compare modified files (`git diff --name-only`) against the Story Shard's `allowed_files`. Any file outside `allowed_files` is an immediate lease violation.
2. **AST Symbol Drift Check (`codegraph:changed_symbols`)**:
   Extract the exact AST symbols modified by the diff to detect drive-by edits inside leased files:
   ```json
   {
     "ServerName": "codegraph",
     "ToolName": "changed_symbols",
     "Arguments": {
       "diff_text": "<git_diff_content>"
     }
   }
   ```
   Verify that every symbol returned by `changed_symbols` is either in `planned_symbols` or a direct private helper required by `planned_symbols`.
3. **Diff Minimalism Check (`clean-diff.sh`)**:
   Run `bash ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/clean-diff.sh` to strip stray whitespace or formatting noise.
4. **Mechanical Stop Gate & Atomic Rollback**:
   - Enforced mechanically by `stop.py` (`_check_subagent_scope_drift`); Builder completion is blocked if files outside `allowed_files` were modified.
   - If scope drift or unintended mutation occurs, revert the unleased changes or restore the pre-wave shadow checkpoint via:
     ```bash
     python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/restore-shadow-checkpoint.py --restore
     ```

### 3. Calculate Drift
- **File Drift**: `actual_unleased_files` (must equal `0`).
- **Symbol / Feature Drift**: `(unexpected_changed_symbols / planned_symbols) * 100`.
- **Include in drift**: Unleased files, unrequested features, drive-by refactors of unrelated functions, unapproved dependencies.
- **Exclude from drift**: Essential bug fixes or type-safety adjustments strictly within `planned_symbols`.

### 4. Escalate When Budget Exceeded
If `actual_unleased_files > 0` or `drift_percent > drift_budget_percent`:
1. **STOP** implementation immediately.
2. Revert out-of-scope hunks or run `restore-shadow-checkpoint.py --restore`.
3. Record the drift event via `mcp__codex_knowledge__knowledge_capture()`.
4. Escalate to `pm` for explicit Story Shard re-leasing — never widen `allowed_files` unilaterally.

### 5. Output Format
```yaml
scope_drift:
  task_ref: <shard_id>
  allowed_files: <list>
  actual_files: <list>
  unleased_files_touched: 0
  planned_symbols: <list>
  actual_changed_symbols: <list from codegraph:changed_symbols>
  orthogonal_edits_detected: 0
  drift_percent: <percentage>
  drift_budget_percent: 5
  status: <within_budget|at_budget|over_budget>
  action: <continue|revert_and_escalate>
```
