# Independent Ensemble Merge Policy

## Core Rules
- **Merge by Evidence, Not Volume**: Every candidate patch must include fresh test execution evidence (`VeriHarness` output) and exact file/line references.
- **Reject Overlapping Writes**: Disjoint Builders must adhere strictly to non-overlapping `allowed_files` leases; any write outside the leased shard is rejected immediately.
- **Blinded Candidate Selection (`Candidate A` vs `Candidate B`)**: When multiple ensemble candidates compete on the same problem, strip author/model metadata and label patches anonymously as `Candidate A` and `Candidate B` before Oracle evaluation.
- **$\Delta_{\text{behav}}$ Tie-Breaking (`KEEP_BASE` Default)**: Evaluate behavioral equivalence and regression deltas ($\Delta_{\text{behav}}$) via the 6-Stage Lexicographic Deliverable Selection Ladder (`../gates/oracle_review_rubric.md`). If $\Delta_{\text{behav}} \le 0$ or candidates tie with baseline behavior, default to `KEEP_BASE` (or select the smallest surgical diff that satisfies all acceptance criteria).
- **Minimalism Invariant**: Preserve the smallest valid result (`clean-diff.sh`) that satisfies the contract with `sec_score == 1.0`.
