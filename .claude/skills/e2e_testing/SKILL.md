---
name: e2e_testing
description: Comprehensive end-to-end QA sweep, release readiness, and bug hunt across workflows, APIs, and regressions.
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# E2E Testing

## Purpose
Run a complete bug sweep after implementation or before release. This skill consolidates QC perspectives into one practical validation pass: black-box user behavior, gray-box contract checks, white-box risk inspection, regression coverage, non-functional testing, and final release evidence.

Use this skill to find defects, not to redesign the product. Keep the sweep proportional to risk, but do not skip relevant layers just because the happy path passes.

## Inputs
- Task contract, acceptance criteria, or user request.
- Current diff and impacted files.
- Project SOT docs, `AGENTS.md`, and native test/regression commands.
- Known risk areas, recent bugs, and user-reported symptoms.

If these are missing, infer a small task contract from the request and mark assumptions explicitly.

## Workflow
1. Establish scope, affected layers, and baseline from project SOT and `AGENTS.md`.
2. Construct the test matrix (smoke, functional, boundary, integration, regression, security, UI).
3. Execute tests outside-in (black-box smoke) then inside-out (white-box logic and edge cases).
4. Compress output into structured findings schema (`severity`, `surface`, `symptom`, `reproduction`, `expected`, `actual`, `evidence`).
5. Enforce completion gates (rerun targeted tests, `auto-verification-harness`, `oracle-review`).

## Visual-Semantic E2E Assertion Trio (`midscene` / `UI-TARS` Pattern)
When executing browser, desktop, or mobile UI E2E flows (`web-infra-dev/midscene` & `bytedance/UI-TARS`), structure steps around three decoupled primitives:
1. **`aiAction` (Goal-Driven Interaction)**:
   - Execute user intent grounded strictly on visible DOM/accessibility `@eN` UIDs or normalized viewport coordinates (e.g., clicking, typing, scrolling, drag-and-drop) without brittle XPath/CSS-class coupling.
2. **`aiQuery` (Structured Typed Data Extraction)**:
   - Extract deterministic, schema-typed JSON state directly from the live rendered viewport (e.g., `{items: string[], total: number, badgeStatus: string}`) to inspect what the user actually sees.
3. **`aiAssert` (Visual-Semantic Invariant Verification)**:
   - Pair natural-language + visual layout invariant checks (zero overlapping controls, zero clipped text `L-16`, zero broken empty states) with deterministic DOM/network assertions (`HTTP 200`, zero console/page errors, state persistence).

## Full Protocol
Load `references/protocol.md` before executing beyond the core rules above.
