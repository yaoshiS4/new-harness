---
name: safety
description: Mutation interception, destructive command prevention, rollback invariants, and worktree isolation.
---

# Safety Rules

## Mutation & Destructive Action Interception
- Ask before adding dependencies, deleting files, changing architecture, applying database migrations, or executing remote git pushes (`--force`, `publish`, `push`).
- Do not auto-learn or capture durable memories from unreviewed or exploratory changes.
- Never invent commands, validation outputs, file paths, or mock test passes.

## Monotonic Progress & Rollback Invariant
- Keep diffs surgical, minimal, and reversible.
- When `test_failure_max_retries` (2) or `same_error_count` (3) is reached, the agent MUST revert uncommitted changes to the last clean commit state before escalating (`git stash` or `git checkout -- <affected files>`). Never leave half-broken speculative diffs in the working tree.

## Isolation & Worktree Governance
- Exactly one write-capable agent per branch or git worktree.
- Read-only roles must stay read-only.
- Subagents return structured summary artifacts only (changed files, verification evidence, remaining risks). No unmediated sibling-to-sibling message loops.

## Model Safety Baseline
- Default to the strongest supported model for orchestration, reasoning, and implementation.
- Fast or mini profiles are reserved strictly for shallow reads, narrow text summaries, or non-critical formatting.

