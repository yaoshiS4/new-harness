---
name: animation-mastery
description: 'Animation engineering: spring physics, curves, duration guidelines, and Apple design motion principles for web/mobile.'
metadata:
  short-description: Motion engineering, curves, spring physics, Apple design
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# Animation Mastery

Engineering motion that **Feels Instant**, inspires **Calm & Trust**, and operates **Effortlessly**. Adapted from Emil Kowalski's animation standards.

## 1. Frequency Gate (Should This Animate?)

| Frequency | Rule | Action |
|-----------|------|--------|
| **100+ times/day / Keyboard shortcuts** | **No animation. Ever.** | Instant state toggle (e.g. command palette, search) |
| **Tens of times/day** | Fast & subtle only | Subtle hover (≤150ms) or color fade |
| **Occasional** | Standard motion | Modals, drawers, toasts, accordion reveals (200-300ms) |
| **Rare / First-time** | Delight budget | Onboarding walkthroughs, celebratory states (300-500ms) |

*Must name purpose*: Feedback, Spatial consistency, State indication, Jarring change prevention, Explanation, or Delight.

## Full Protocol
Load `references/protocol.md` before executing beyond the core rules above.
