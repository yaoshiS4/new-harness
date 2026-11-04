---
name: ui-ux-craft
description: UI/UX design systems, layout ergonomics, motion physics, rendering performance, and accessible styling.
---

# UI/UX Craft & Frontend Engineering Standards

Deliver production-grade, visually refined, and jank-free user interfaces enforcing the **5 Feels** (**Zero Hesitation**, **Calm & Trust**, **Brain Relax**, **Feels Instant**, **Effortless**) and strict technical invariants across web and mobile platforms.

## Design Direction & Workflow Standards

### 1. Aesthetic Direction & Design Read
- Understand the brief before choosing the visual direction: audience, domain, tone, brand assets, and quiet constraints (accessibility, trust).
- Commit to one specific, cohesive aesthetic direction; strictly avoid generic AI defaults.
- Design the real interface with all interactive states, responsive collapse, and real or realistic assets.
- Pre-work for design tokens: Before creating or modifying design tokens, call `call_mcp_tool(ServerName="codex_knowledge", ToolName="project_context")` to check existing project tokens and `call_mcp_tool(ServerName="codegraph", ToolName="callers_callees")` to trace consuming components.

### 2. Core Pillars & Apex Standards
- **Rendering Performance & Frame Budgets (Feels Instant)**:
  - *60fps / 120fps Invariant*: Zero dropped frames during scrolling, gesture drags, and view transitions.
  - *Layout Stability (CLS = 0)*: Explicitly pre-reserve component dimensions (`aspect-ratio`, explicit width/height) before images or async data load.
  - *Zero Layout Thrashing*: Batch DOM reads before writes. Use CSS `contain: content` and `content-visibility: auto` on off-screen lists.
  - *Perceived Speed*: Skeleton loaders or progressive reveal on async fetch — never blank containers.
- **Craft Self-Review**: Mobile + desktop responsive fit, Vietnamese diacritic clearance (`lineHeight >= 1.45x`), interactive pressed/active states, and at least one memorable, refined signature quality.

## Full Protocol
Load `references/protocol.md` before executing beyond the core rules above.
