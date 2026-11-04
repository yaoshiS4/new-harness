---
description: Run the independent Oracle audit on a plan (appends the Oracle Hardening sign-off section) or on the current diff (correctness, scope drift, test evidence, hallucination audit). Satisfies the Stop hook's plan and verification gates.
argument-hint: [plan | diff] [path]
---

# /oracle-review

Target: $ARGUMENTS (default: `diff`; use `plan` to sign off `implementation_plan.md`).

1. Collect the three Oracle inputs (O-R1) and nothing else:
   - the spec / Story Shards (`implementation_plan.md`, `task.md`, or the inline shard from chat),
   - the clean diff: `bash antigravity/scripts/clean-diff.sh` (or `git diff HEAD`),
   - fresh verification logs produced this turn (`set -o pipefail; <verification_cmd> 2>&1 | tail -n 60`).
2. Dispatch `oracle-review` with those inputs (<= 6,000 chars; put long diffs in a scratch file and pass the path). For medium or larger changes also dispatch `hallucination-auditor` in parallel.
3. Plan mode: the Oracle appends only `## Oracle Hardening, Directives & Verification Matrix` with `oracle_sign_off{reviewer, verdict, scope_drift_observed, binding_directives, signed_at}` to `implementation_plan.md`; sync new mandates into `task.md`.
4. Diff mode: verdict PASS / CONDITIONAL / FAIL with `[Evidence: path:line | snippet]` findings. CONDITIONAL -> fix in place with the owning builder, re-run the failed checks only. FAIL -> revision gate (max 2 attempts) then escalate.
5. After PASS only: `mcp__codex_knowledge__knowledge_capture(slug, key, value, source_ref)` for durable lessons; update `docs/STATUS.md`.
