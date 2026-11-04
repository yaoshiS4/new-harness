# System Baseline Metrics (Pre-Implementation Baseline - August 2026)

Recorded as required by Oracle Directive D6 prior to harness modernization.

## 1. Tool Output Baselines (Uncompressed)
- `grep_search`: ~20-50 lines per query (raw file matches with full lines).
- `view_file`: 50-200 lines per read (frequently whole function or file chunks).
- `run_command` (build / test / lint): 20-100 lines (contains build logs, progress bars, verbose outputs).
- Error diagnosis latency: 2-3 turns due to large stdout noise diluting stderr tracebacks.

## 2. Token & Governance Footprint
- Current active rules in `rules/`: 5 files (`core.md`, `coordination.md`, `oracle.md`, `safety.md`, `token_economy.md`).
- Current guardrails in `guardrails/`: 7 files.
- Phantom tool references detected in rules/workflows: 4 (`cognition_codex_*`, `evolution_*`, `trace_export_*`, `cognition_codex_check_aop_consistency`).
- Fast-Track bypass integrity: Baseline is unstructured (no formal firewall).

## 3. Target Post-Implementation Verification Metrics
- Tool output size reduction for informational/success runs: >= 50% via RTK compression.
- Error traceback preservation: 100% (zero truncation on non-zero exit codes).
- Phantom tool references remaining in runtime config/rules: 0.
- Governance budget cap: <= 5 new files, each < 50 lines.
- Fast-Track firewall: 100% bypass of multi-agent/loop governance on atomic tasks (<= 3 files).
