---
description: Path 2 Normal Route (4-10 files or 2 domains) - the 8-stage pipeline with explorers, PM contract (implementation_plan.md + task.md), disjoint leased builders, two-stage QC, and independent Oracle audit.
argument-hint: <feature or change request>
---

# /standard-dev — Path 2 (8-stage pipeline)

Request: $ARGUMENTS

You are the PM. Stages run in order; each stage ends with `[Step N of 8 Done: ...] -> Next: ...`.

1. **Intake**: ground against SOT docs (`docs/STATUS.md`, `docs/README.md`, `CLAUDE.md`, `AGENTS.md`, `README.md`) and `mcp__codex_knowledge__project_context`. Confirm Path 2 (4-10 files or 2 domains); otherwise reroute to `/fast-track` or `/goal`.
2. **Enrichment**: dispatch `backend-explorer` and/or `frontend-explorer` (read-only, sonnet) in parallel for coordinates, dependencies, candidate tests. Use `research-explorer` only for third-party API questions.
3. **Clarification (scope lock)**: ask the user only what the repo cannot answer (AskUserQuestion, recommended option first). Freeze the drift budget (5%).
4. **PM contract**: write `implementation_plan.md` (sections 1-7; `sa` for cross-component design) and `task.md` with BMAD Story Shards: non-overlapping `allowed_files`, immutable acceptance criteria, `verification_cmd` per shard, `oracle_custody_lease`. Then obtain plan sign-off: `oracle-review` appends `## Oracle Hardening, Directives & Verification Matrix` (the Stop hook blocks completion until it exists).
5. **Disjoint builders**: `dev-fe` for UI shards, `dev-be`/`debugger` for backend shards (max 2 concurrent). Each Agent prompt carries its shard verbatim (`allowed_files:` mandatory, <= 6,000 chars).
6. **Surgical implementation**: builders work TDD inside their lease and return summary + fresh verification output. Re-dispatch the same builder for minor revisions; re-plan for major ones.
7. **Two-stage QC**: 7a `frontend-qc` (read-only UI audit) for UI shards; 7b `test-runner` (targeted tests, lint, `tsc --noEmit`). Route `Fail: path:line` findings back to the owning builder.
8. **Independent Oracle audit**: `oracle-review` (+ `hallucination-auditor` for medium+ tasks) on the clean diff with fresh logs. On PASS: update `docs/STATUS.md`, `mcp__codex_knowledge__memory_store` for validated lessons only, optional `doc-sync-worker`. On FAIL: revision gate, max 2 attempts, then escalate to the user.
