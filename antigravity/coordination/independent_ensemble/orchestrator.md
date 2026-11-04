# Independent Ensemble Orchestrator

## Orchestration Protocol
- **Disjoint Parallel Execution**: Use when multiple bounded Builders (`TypeName: "self"`, `Model: "inherit"`) or read-only reviewers (`TypeName: "research"`, `Model: "flash"`) can execute concurrently across isolated git worktrees (`worktree-isolation`).
- **Explicit Non-Overlapping Leases**: Assign each worker an explicit BMAD Story Shard with disjoint `allowed_files` and `Oracle-Custody-Lease` settings (`NONE` by default).
- **Blinded Candidate Tournament (`Candidate A` / `Candidate B`)**: For competitive synthesis or high-risk bug fixes, anonymize competing proposals as `Candidate A` and `Candidate B` prior to Stage 8 Oracle review.
- **Evidence-Based Merging & $\Delta_{\text{behav}}$ Tie-Breaker**: Require machine-dense telemetry returns (diffs + test logs). Apply $\Delta_{\text{behav}}$ tie-breaking where ties or zero behavioral gains resolve to `KEEP_BASE`.
