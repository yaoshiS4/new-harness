---
description: Full harness system audit - runs the verification gate, tree validator, compiled QC, and the harness-deficiency-audit skill, then produces the 10-section audit report (executive assessment, highest-impact problems, keep/remove/consolidate, migration order, verdict).
argument-hint: [harness | codebase | both]
---

# /system-audit

Mode: $ARGUMENTS (default `harness`; `codebase` audits the product repo; `both` runs both vectors).

## Pre-steps (fresh output required)
1. `set -o pipefail; bash scripts/verify-claude-harness.sh 2>&1 | tail -n 40` (6 gates).
2. `python3 scripts/validate-claude-tree.py` (byte budget, skill coverage, braces, hooks/agents/commands, CP-2 security guardrails; sec_score must stay 1.0).
3. `python3 antigravity/scripts/run-compiled-qc.py` on changed files when a product codebase is in scope.
4. Load the `harness-deficiency-audit` skill; Mode A vectors: rule conflicts, loops/deadlocks, token economy, hook contracts (PreToolUse `permissionDecision`, PostToolUse `additionalContext`/`updatedToolOutput`, Stop `decision: block`), drift, anti-hallucination. Mode B vectors: architecture, loops/races, error handling, leaks, test integrity, security.
5. Pull telemetry: `harness_failures` by failure_type and severity from `~/.local/share/codex/projects/registry.sqlite` (read-only `sqlite3` or `python3 -c`), plus `~/.cache/claude_harness/sessions/*/flags`.

## Report (10 sections, uncapped lists, evidence as `[Evidence: path:line | snippet]`)
1. Executive Assessment (10-15 bullets)
2. Evidence & Scope
3. Usage & Value Matrix
4. Highest-Impact Problems (`[AG-xx]`: Evidence / Impact / Root Cause / Recommendation / Confidence)
5. Keep / Remove / Consolidate / Upgrade
6. External Benchmarks (Claude Code native features, OpenCode, BMAD)
7. Architecture vNext
8. Top 10 Config Changes
9. Migration Order (3 phases)
10. Final Verdict
