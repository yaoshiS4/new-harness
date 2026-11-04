# Runtime Handoff Workflow

Switch the same project between Codex, OpenCode, and Antigravity without conflicts.

## Why
Multi-runtime handoff ensures shared state is safe across tools without concurrent write conflicts.

## Session Start (any runtime)
1. Read `docs/HANDOFF.md` in the project if present (previous tool's state).
2. Run inter-session cache hygiene and housekeeping (`python3 /home/heocop/.gemini/antigravity/scripts/housekeeping.py`).
3. Read-only file exploration, review, or planning may run without conflicts.
4. Check `docs/HANDOFF.md` or git status before applying new changes.

## First Write
- Parallel writes across tools are allowed only in separate git worktrees on separate branches (worktree-isolation skill).

## Session End / Tool Switch
1. Update `docs/HANDOFF.md` in the project:
   - completed items, in-progress item, next actions
   - validation state (exact commands run and results)
   - unresolved questions / risks
2. Record validated durable knowledge via `call_mcp_tool` on `codex_knowledge` (`knowledge_capture`, `memory_store`, or `handoff_write`).
3. Run `python3 /home/heocop/.gemini/antigravity/scripts/housekeeping.py` to clean temporary session flags.
4. The next tool starts from step 1 of Session Start and resumes without re-exploration.

## Conflict Rules
- A stale `docs/HANDOFF.md` (claims already in git history) is refreshed, never trusted blindly.
- Takeover without the user's explicit approval is a contract violation (scope-drift-control reports it).
- Never delete another runtime's lock file by hand; use `release` with the holder's runtime name only with user approval.
