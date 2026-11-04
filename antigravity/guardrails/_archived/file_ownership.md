# File Ownership Guardrails

## Single Writer Rule
- One writer per branch or worktree
- No sibling-to-sibling messaging
- Each write-capable agent has one branch or worktree

## Subagent Boundaries
- Subagents are explicit, bounded, and non-overlapping
- Read-only roles stay read-only
- Summary-only returns: changed files, evidence, risks, next action

## Delegation
- `pm` decides whether to delegate, spawn subagents, or run a multi-agent wave
- `pm` owns the task contract, validation target, scope drift budget, and final handoff
- Use one writer per branch
