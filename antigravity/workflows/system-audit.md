---
name: system-audit
summary: Forensic audit and optimization workflow for runtime environments, codebase performance, and agent harnesses.
---

# System Audit & Optimization Workflow

## Purpose
Perform deep forensic analysis of runtime configurations, session logs, tool usage patterns, latency/token efficiency, and architectural integrity.

## Mechanical Verification & Audit Pipeline

Before compiling the 10-section report, run the automated harness verification suite and activate the `harness-deficiency-audit` skill:

1. **Full Harness Verification Gate (`verify-harness.sh`)**:
   - Execute `bash scripts/verify-harness.sh` to validate all 6 harness layers (hook unit test suites, local MCP server pytest suites, and mechanical tree validation).
2. **Mechanical Harness Tree & Security Invariant (`validate-harness-tree.py`)**:
   - Execute `python3 antigravity/scripts/validate-harness-tree.py` to enforce CP-2 Security Guardrail Integrity (`sec_score == 1.0`), skill/script registration parity, and the `<= 12,000` character budget on `antigravity/GLOBAL_AGENTS.md`.
3. **Compiled QC & Static Invariant Sweep (`run-compiled-qc.py`)**:
   - Execute `python3 antigravity/scripts/run-compiled-qc.py` to run deterministic static checks, contract schema validation, and anti-slop lint rules.
4. **Harness Deficiency Audit (`harness-deficiency-audit`)**:
   - Apply `antigravity/skills/harness-deficiency-audit/SKILL.md` to diagnose token bloat, JEV loop vulnerabilities, model routing drift, and dead skill references.

## 10-Section Audit Standard

1. **Executive Assessment**: 10–15 bullet points on what is working, major waste, accuracy problems, and architectural direction.
2. **Evidence & Scope**: Document number of sessions inspected, configuration areas, external projects researched, and assumptions.
3. **Usage & Value Matrix**: Consolidated table evaluating Component, Type, Observed Usage, Value, Waste/Risk, Recommendation, Confidence.
4. **Highest-Impact Problems**: Prioritized findings using the `[AG-xx]` format with Evidence, Impact, Root Cause, Recommendation, Confidence.
5. **Keep / Remove / Consolidate / Upgrade**: Clear triage of all active components.
6. **External Benchmark Findings**: Comparison against relevant external patterns (OpenCode, Claude Code, DeepSeek, BMAD).
7. **Recommended Architecture vNext**: Minimalist, high-leverage architectural diagram and workflow.
8. **Top 10 Configuration Changes**: Actionable change matrix prioritized by ROI.
9. **Migration Order**: 3-phase execution order with simple success criteria.
10. **Final Verdict**: Summary of biggest strength, biggest weakness, highest-value change, and anti-patterns to avoid.
