---
description: Path 1 Quick Route (<= 3 files, 1 domain, no schema/auth/migration risk) - inline Story Shard, one leased builder, fast verification gate. PM never edits code.
argument-hint: <task description>
---

# /fast-track — Path 1 Quick Route

Task: $ARGUMENTS

Run the Antigravity fast-track workflow on Claude Code. You are the PM (root thread); you orchestrate, you do not edit application code.

## 1. Intake & inline Story Shard (~2 min)
1. Ground: read `docs/STATUS.md` / `CLAUDE.md` / `AGENTS.md` / `README.md` if present; `mcp__codegraph__symbol_lookup` or Grep (`head_limit` 50) to locate the exact coordinates.
2. Confirm Path 1 criteria: <= 3 files, 1 domain, zero schema/auth/migration/dependency risk, clear intent. If any criterion fails, switch to `/standard-dev`.
3. Emit the inline shard in chat (no `implementation_plan.md`):
```yaml
story_shard:
  shard_id: P1-<slug>
  owner_role: dev-fe | dev-be | debugger
  allowed_files: [<exact paths>]
  acceptance_criteria: [<immutable, testable>]
  verification_cmd: "<targeted test / typecheck command>"
  oracle_custody_lease: NONE
```

## 2. Delegated builder fix
Call the Agent tool once: `subagent_type` = the owner role; the prompt MUST include the `allowed_files:` block, acceptance criteria, and `verification_cmd` (<= 6,000 chars). Model stays at the role baseline (no `opus`/`fable` escalation without asking).

## 3. Fast verification gate
1. Independent check: run the `verification_cmd` yourself (or `test-runner` for larger suites) and `tsc --noEmit` / `py_compile` where relevant; use `set -o pipefail` when piping.
2. UI changes: `frontend-qc` read-only pass (no nested cards, icon fatigue, ellipsis clipping).
3. `bash antigravity/scripts/clean-diff.sh` (or `git diff --stat`) to confirm drift = 0 against `allowed_files`.
4. Report: `[Step 3 of 3 Done: verified] -> Next: <one action>` with the fresh verification output.
