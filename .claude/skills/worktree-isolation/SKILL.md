---
name: worktree-isolation
description: Manages git worktrees for safe parallel agent execution and isolated branch development.
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# Worktree Isolation Skill

## Purpose
Prevent file collisions and state corruption when multiple write-capable Builder subagents execute in parallel by isolating each Builder in a dedicated Git worktree (the Agent tool's `isolation: "worktree"` option or `git worktree add`), enforced by baseline and pre-merge verification gates.

---

## When to Use
- Multiple write-capable Builders (`subagent_type: "dev-fe" | "dev-be" | "debugger"`) need to modify files simultaneously (Path 3 Wave-Isolated Builders)
- Parallel implementation of disjoint Story Shards
- Running experimental refactors or risky migrations where instant atomic rollback is required

---

## 1. Native Subagent Workspace Isolation (the `Agent` tool)
When launching parallel Builders via the `Agent` tool, prefer Claude Code's built-in isolation before manual shell worktree management:
- **`isolation: "worktree"` (Recommended for parallel write waves)**: the subagent runs in a temporary git worktree created from the default branch (under `<repo>/.claude/worktrees/`), so concurrent Builders never collide; the worktree is auto-cleaned when it carries no changes. Merge survivors back with `git merge --no-ff` after the Pre-Merge Gate.
- **No isolation (shared working tree)**: only safe for read-only Explorers / QC, or strictly sequential single-Builder waves with non-overlapping `allowed_files`.
- The main thread can also isolate itself with `claude --worktree <name>` or the `EnterWorktree` tool for risky refactors.

---

## 2. Manual Git Worktree & Baseline Gate (`obra/superpowers` — `using-git-worktrees`)

### Step 1: Create Worktree & Verify Directory Ignore Rules
```bash
git worktree add ../<branch-name> -b <branch-name>
```

### Step 2: Run Clean Baseline Verification Inside the Worktree (Mandatory Pre-Work Gate)
Before the Builder writes a single line of code inside the worktree, verify that the worktree starts from a 100% passing baseline:
```bash
# Verify clean test baseline inside the isolated worktree before applying changes:
python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/select-affected-tests.py --workspace ../<branch-name>
```
- If the baseline test suite fails before any edits, **abort or report the pre-existing broken baseline** instead of conflating baseline failures with Builder changes.

### Step 3: Lock File Registration (`.agent-locks/`)
Each active Builder's lease is registered by the orchestrator in `task.md` (and optionally `.agent-locks/<agent-name>.json`, git-ignored) as:
```json
{
  "agent": "<agent-name>",
  "task_id": "<story-shard-or-task-id>",
  "oracle_custody_lease": "<Oracle-Custody-Lease-ID>",
  "lifecycle_state": "ACTIVE",
  "branch": "<branch-name>",
  "workspace_mode": "worktree",
  "worktree": "<path>",
  "allowed_files": ["<claimed files>"],
  "started_at": "<ISO timestamp>",
  "expires_at": "<ISO timestamp>"
}
```
1. Only one write-capable agent may claim a file at a time.
2. Locks expire after 30 minutes by default.
3. Agents must verify zero lock overlap before writing; the `pm` orchestrator resolves lock conflicts.

---

## 3. `s12_worktree_task_isolation` Task-to-Worktree State Binding (`shareAI-lab/learn-claude-code`)

Every isolated worktree MUST be bound 1-to-1 to an explicit `task_id` and `oracle_custody_lease` and progress through a strict 3-state atomic lifecycle (`PREPARED -> ACTIVE -> MERGED_OR_DISCARDED`):

1. **`PREPARED` (Worktree Created & Baseline Verified)**:
   - The worktree directory (`../<branch-name>` or the Agent tool worktree) is provisioned, bound to `(task_id, oracle_custody_lease)`, and passes the mandatory pre-work baseline check (`select-affected-tests.py`). Zero edits are permitted before reaching `ACTIVE`.
2. **`ACTIVE` (Lease Claimed & Surgical Execution)**:
   - The Builder subagent acknowledges its `allowed_files` lease (`s10` ack), transitions the lock record to `ACTIVE`, and performs mutations strictly within its leased paths.
3. **`MERGED_OR_DISCARDED` (Terminal Cleanup & Lock Release)**:
   - Upon passing the Pre-Merge Gate, changes are merged (`--no-ff`) into the target branch, OR upon failure/abandonment, the worktree is discarded without polluting the main branch.
   - In both terminal outcomes, the worktree directory is removed (`git worktree remove`), the lock entry transitions to `MERGED_OR_DISCARDED`, and the terminal receipt is checkpointed via `codex_knowledge:handoff_checkpoint`. Orphaned worktrees without an active `task_id` lease are pruned automatically.

---

## 4. Pre-Merge Verification & Finishing a Branch (`obra/superpowers` — `finishing-a-development-branch`)

Never merge a worktree branch back into the main workspace without passing the 3-step Pre-Merge Gate:

1. **Scope Lease & Clean Diff Check**:
   ```bash
   git -C ../<branch-name> diff --name-only
   ```
   Verify that modified files strictly match the Story Shard's `allowed_files` and zero ephemeral artifacts (`.venv/`, `__pycache__/`, `.pytest_cache/`, `*.db*`, `*.log`) exist.
2. **In-Worktree Test & Compile Execution**:
   Run the Story Shard's `verification_cmd` inside `../<branch-name>` and require `exit_code: 0`.
3. **Commit, Merge (`--no-ff`), and Prune**:
   ```bash
   git -C ../<branch-name> add -A
   git -C ../<branch-name> commit -m "<message>"
   git merge <branch-name> --no-ff
   git worktree remove ../<branch-name>
   git branch -d <branch-name>
   ```
4. **Emergency Rollback via Shadow Checkpoint**:
   If a merge conflict or post-merge regression corrupts the main workspace, restore the pre-wave shadow checkpoint via:
   ```bash
   python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/restore-shadow-checkpoint.py --restore
   ```

### Cleanup Stale Locks
```bash
# Remove locks older than 30 minutes (bounded with --max-results 50)
fd -e json --changed-before 30m --max-results 50 . .agent-locks/ -x rm {}
```

---

## Guardrails
- Never run two write-capable Builders on the same branch/worktree simultaneously without disjoint file locks.
- Always run baseline verification before starting work and pre-merge verification before merging.
- Clean up worktrees, temporary branches, and `.agent-locks/` entries immediately after merge.
- Record worktree handoff state via `mcp__codex_knowledge__handoff_checkpoint()` for cross-agent visibility.
