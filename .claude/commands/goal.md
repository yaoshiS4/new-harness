---
description: Path 3 Long-Horizon Route (> 10 files, >= 3 domains, migrations, new subsystems) - parallel 3-explore, architect spec and ADRs, unlazy depth tree (PLAN.md + GATES.md), adversarial plan gate, wave-isolated builders in worktrees, checkpoints, 3-round zero-bug loop, doc sync.
argument-hint: <epic / goal statement>
---

# /goal — Path 3 Long-Horizon (SOL sequential)

Goal: $ARGUMENTS

You are the PM. Never edit application code; orchestrate the eight phases below and anchor every message with `[Step N of 8 Done: ...] -> Next: ...`.

1. **Parallel 3-Explore**: dispatch `backend-explorer`, `frontend-explorer`, `research-explorer` concurrently (read-only, sonnet). Collect three briefs: affected symbol coordinates, dependencies, candidate tests.
2. **Architect spec & ADR**: `sa` produces the technical spec, C4 topology, NFRs, ADRs (>= 2 options with tradeoffs) and bounded interfaces; no feature code.
3. **PM depth tree (unlazy)**: write `PLAN.md` and `GATES.md` (leaf gates with mechanical `CHECK:` + `EXPECT:` markers) and split the work into BMAD Story Shards with disjoint `allowed_files`. Preload the `unlazy` skill for the template contract.
4. **Adversarial plan gate**: `critical-planner` pre-mortem + `verify-oracle.sh --plan` if `scripts/verification/` exists (scaffold with `python3 antigravity/scripts/ensure-verification-gates.py .` after user approval). Revise until APPROVE; `oracle-review` signs the plan.
5. **Wave-isolated builders**: follow `worktree-isolation`; at most 2 concurrent builders (`dev-fe` / `dev-be` / `debugger`), each in its own worktree/branch with its shard lease. One writer per branch.
6. **Context checkpointing**: at 60% context (status line) or 8 user turns without completion: `mcp__codex_knowledge__handoff_checkpoint(slug, "sol:<task>:<phase>", payload)`, record the break-resume contract in `docs/STATUS.md`, then `/compact` (the PreCompact hook snapshots state; the next prompt restores it).
7. **3-round zero-bug loop**: `test-runner` + `frontend-qc` + `oracle-review`/`hallucination-auditor` over the clean diff until three consecutive clean rounds (`test-3-round-loop.sh` when scaffolded). Defects go back to the owning builder; drift > 5% reopens the scope lock.
8. **Doc sync & release gate**: `doc-sync-worker` updates `docs/STATUS.md`, README, traceability, and the knowledge graph; run the release gate (diff matches contract, 0 test failures, 0 typecheck errors, no secrets via `rg -m 50`, dependencies pinned and audited, Oracle PASS). Verdict SHIP / HOLD / BLOCK.
