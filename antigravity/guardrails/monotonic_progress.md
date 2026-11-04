# Monotonic Progress Guardrails

## 3-Tier Adaptive Routing Alignment
Every task must be classified into one of three execution paths:
- **Path 1: Quick Route (`<= 3` files, 1 domain, zero schema/auth/migration risk)**:
  - Fast-track: Intake & Inline Story Shard -> Delegated Builder Fix -> Fast Verification Gate (unit test + `tsc --noEmit` + UI anti-slop check).
- **Path 2: Normal Route (`4–10` files or 2 domains, standard features/refactors)**:
  - 8-Stage Pipeline: `1. Intake -> 2. Enrichment -> 3. Clarification -> 4. PM Contract & Story Shards -> 5. Disjoint Specialist Builders -> 6. Surgical Implementation -> 7. Two-Stage QC -> 8. Independent Oracle Audit`.
- **Path 3: Long-Horizon Route (`> 10` files, `>= 3` domains, new subsystems/migrations)**:
  - Deep Orchestration: Parallel 3-Explore -> Architect Spec & ADR -> PM Depth-Tree & Story Shards (`PLAN.md` + `GATES.md`) -> Adversarial Plan Gate -> Wave-Isolated Builders in Git Worktrees -> Context Checkpointing -> 3-Round Zero-Bug Loop -> Doc Sync.

## Surgical Changes & Progress Tracking
- Keep diffs surgical, minimal, and reversible.
- Progress strictly advances across the 8-Stage Pipeline:
  - `1. Intake`: Ground request against project SOT docs (`docs/STATUS.md`, `AGENTS.md`).
  - `2. Enrichment`: Read-only exploration (`TypeName: "research"`, `Model: "flash"`).
  - `3. Clarification`: Elicit ambiguous requirements via `ask_question`.
  - `4. PM Contract & Story Shards`: Author `implementation_plan.md` + `task.md` with leased `allowed_files`.
  - `5. Disjoint Specialist Builders`: Lease bounded story shards to disjoint builder agents.
  - `6. Surgical Implementation`: Builder modifications strictly confined to leased paths.
  - `7. Two-Stage QC`: 7a Static code/UI anti-slop audit + 7b Dynamic test runner execution.
  - `8. Independent Oracle Audit`: Mandatory independent verification before release or merge.
- Memory capture: Only after validation and Oracle approval.

## Loop Governance
- All major processes are governed loops per `../coordination/loop_engineering.md` with bounded iteration, reflection, and early-stop.
- Self-evolution follows the SkillOpt protocol per `../skills/harness-deficiency-audit/SKILL.md` (Section 7).
- Dreaming/Sleep consolidation runs at session end or token budget > 90% per `../workflows/dreaming-consolidation.md`.
