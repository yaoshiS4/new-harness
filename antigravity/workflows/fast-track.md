---
name: fast-track
summary: Path 1 Quick Route execution for atomic fixes and narrow refactorings (<= 3 files).
---

# Path 1: Quick Route Workflow (Atomic <= 3 Files)

## Purpose
Execute atomic bug fixes, narrow refactorings, and single-domain tasks (`<= 3` files, 0 schema/auth/migration risk) rapidly with strict role isolation: Root Orchestrator / PM frames an inline Story Shard and delegates implementation to a single Builder subagent (PM never mutates application source code in-session).

## Execution Sequence

```
1. Intake & Inline Story Shard ──> 2. Delegated Builder Fix ──> 3. Fast Verification Gate
```

### Step 1: Intake & Inline Story Shard (PM / Orchestrator)
- Ground raw user request against project SOT (`docs/STATUS.md`, `docs/README.md`, `AGENTS.md`) and symbol index (`codegraph` / `rg`).
- Verify task qualifies for **Path 1: Quick Route**:
  - Touches $\le 3$ files in 1 domain/package.
  - Zero schema, migration, dependency, auth, or architectural changes.
  - Well-defined intent and unambiguous scope.
- Emit an **Inline Story Shard** in chat (zero `implementation_plan.md` ceremony):
  - **Target Files (`allowed_files`)**: explicit bounded paths.
  - **Acceptance Criteria (ACs)**: concrete, verifiable testable outcomes.
  - **Verification Command**: targeted test or typecheck command.

### Step 2: Delegated Builder Fix (Builder Subagent)
- Orchestrator spawns 1 Builder subagent (default `Model: "inherit"`; escalating to `Model: "pro"` requires `force_ask` / `ask_question`):
  `invoke_subagent TypeName: "self", Role: "dev-fe" | "dev-be" | "debugger", Model: "inherit"`
- **Strict Role Isolation Invariant**: The Root Orchestrator (`pm`) **NEVER** directly edits application source code (`apps/**`, `packages/**`, `src/**`, `*.ts`, `*.tsx`, etc.). All code modifications are executed strictly by the Builder subagent within its leased `allowed_files`.
- For UI/UX changes: Builder strictly adheres to `guidelines/ui-apex-invariants.md` and `guidelines/anti-slop-taxonomy.md`.

### Step 3: Fast Verification Gate (QC & Validation)
- Run targeted unit test(s) for touched behavior (e.g. `npm test -- path/to/test`).
- Run compiler/typecheck: `tsc --noEmit`.
- **UI Anti-Slop Check**: If UI components were touched, perform a mandatory anti-slop check to ensure zero nested cards, no icon fatigue, and no ellipsis clipping.
- Verify clean diff via `scripts/clean-diff.sh`.
