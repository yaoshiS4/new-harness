---
name: standard-dev
summary: Path 2 Normal Route execution for standard features, tactical refactors, and multi-component tasks (4–10 files / 2 domains).
---

# Path 2: Normal Route Workflow (Standard / Tactical — 4–10 Files / 2 Domains)

## Purpose
Deliver non-trivial features, tactical refactors, and multi-component changes (4–10 files or 2 domains) with guaranteed role isolation, BMAD Story Shard ownership, and two-stage read-only quality control.

## 8-Stage Execution Sequence

```
1. Intake ──> 2. Enrichment ──> 3. Clarification ──> 4. PM Contract & Story Shards ──> 5. Disjoint Specialist Builders ──> 6. Surgical Implementation ──> 7. Two-Stage QC ──> 8. Independent Oracle Audit
```

### Stage 1: User Feedback Intake
- Ground raw user request against project SOT (`docs/STATUS.md`, `docs/README.md`, `AGENTS.md`) and local codebase.

### Stage 2: Enrichment (Research / Flash)
- Dispatch read-only explorer subagents (`TypeName: "research"`, `Role: "frontend-explorer" | "backend-explorer"`, `Model: "flash"`).
- Enrich domain context, design specs, and CodeGraph telemetry (`sot-context`, `codegraph`).

### Stage 3: Clarification (Scope Lock)
- Resolve requirements, acceptance criteria, and out-of-scope boundaries (`requirement-interviewer` / `ask_question`). Freeze scope drift budget.

### Stage 4: PM Contract & BMAD Story Shards Formulation
- Root Orchestrator (`pm`) generates `<appDataDir>/brain/<conversation-id>/implementation_plan.md` and companion `task.md`.
- Formulate **BMAD Story Shards** with strict ownership boundaries:
  - **Allowed Files (`allowed_files`)**: explicit, non-overlapping file lists per shard.
  - **Immutable ACs**: deterministic criteria and invariants.
  - **Verification Command**: exact targeted test and lint command per shard.
- **Strict Role Invariant**: PM orchestrates and drafts contracts; PM **NEVER** modifies application source code (`apps/**`, `packages/**`, `src/**`, etc.).

### Stage 5: Disjoint Specialist Builders Assignment
- Spawn specialist Builders for each disjoint Story Shard (`Model: "inherit"` default; escalating to `"pro"` requires `force_ask`):
  - Frontend: `invoke_subagent TypeName: "self", Role: "dev-fe", Model: "inherit"`
  - Backend / Core: `invoke_subagent TypeName: "self", Role: "dev-be" | "debugger", Model: "inherit"`
- Ensure non-overlapping file leases (`allowed_files`).

### Stage 6: Surgical Implementation (TDD Cycle)
- Builders execute implementation strictly within leased files:
  - TDD progression: Interfaces $\rightarrow$ Unit Tests $\rightarrow$ Implementation.
  - Adhere to `ui-apex-invariants.md` and `anti-slop-taxonomy.md`.
  - Builders never mutate files outside their assigned Story Shard.

### Stage 7: Two-Stage Read-Only QC
- **Stage 7a (Static UI / Anti-Slop QC)**:
  - Inspector: `invoke_subagent TypeName: "self", Role: "frontend-qc", Model: "inherit"`.
  - Strictly read-only audit of UI components against `guidelines/ui-apex-invariants.md` and `guidelines/anti-slop-taxonomy.md` (no nested cards, no icon fatigue, no badge proliferation, no ellipsis clipping).
  - Never self-edits code; passes defect list `Fail: <path:line>` back to the Builder.
- **Stage 7b (Dynamic Test & Linter Execution)**:
  - Runner: `invoke_subagent TypeName: "research", Role: "test-runner", Model: "flash"`.
  - Executes targeted tests, full package test suites, linter, and `tsc --noEmit`.

### Stage 8: Independent Oracle Audit
- Inspector: `invoke_subagent TypeName: "self", Role: "oracle-review" | "hallucination-auditor", Model: "inherit"` (`"pro"` requires `force_ask`).
- Run `bash scripts/verification/verify-oracle.sh` (when present, or scaffolded via `ensure-verification-gates.py`).
- Review clean diff via `scripts/clean-diff.sh` against the High-Precision Defect Taxonomy and AgentHallu checks before final delivery.
