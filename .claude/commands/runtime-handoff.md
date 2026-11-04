---
description: Multi-runtime handoff protocol (Claude Code <-> Codex / OpenCode / Antigravity) - read or refresh docs/HANDOFF.md, checkpoint to codex_knowledge, run housekeeping, respect lock and worktree rules.
argument-hint: [start | end]
---

# /runtime-handoff

Phase: $ARGUMENTS (default `start`).

## start
1. Read `docs/HANDOFF.md` if present (completed / in-progress / next actions / validation results / open risks). A stale handoff is refreshed, never trusted.
2. `python3 antigravity/scripts/housekeeping.py --dry-run` (then without `--dry-run` if safe) to sweep caches and checkpoint SQLite WALs.
3. `git status --short` and `git worktree list`; never delete another runtime's lock file (`.agent-locks/`) manually. Parallel writes only in separate worktrees on separate branches.
4. `mcp__codex_knowledge__handoff_read(slug, name)` for the latest checkpoint; `mcp__codex_knowledge__project_context(slug)` for grounding.

## end
1. Update `docs/HANDOFF.md`: completed, in-progress, next actions, validation commands + fresh results, open questions and risks.
2. `mcp__codex_knowledge__handoff_checkpoint(slug, "<runtime>:<task>:<phase>", payload)` and `knowledge_capture` for validated lessons.
3. Run housekeeping; leave no `.venv/`, `__pycache__/`, `*.log`, or stray outputs in the repo.
4. Taking over another runtime's in-progress work without user approval is a violation; ask first.
