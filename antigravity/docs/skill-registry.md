# Skill Registry: Antigravity Global Skills Index

## Purpose
Index native Antigravity skills for task-scoped progressive disclosure, harness activation, and 1% context budget cap enforcement.

## Context Budget Invariant (MR-5)
- All skill descriptions in active prompts must not exceed **1% of model context window** (hard cap $\le 1536$ characters per skill description).
- Unused skills must use on-demand progressive loading rather than being injected into Tier A system prompts.

---

## 1. Diagnostics, Debugging & Runtime Repair

| Skill | Type | Target Roles | Core Capabilities | Budget Status |
| :--- | :--- | :--- | :--- | :--- |
| `loop-detection` | standalone | all agents | Stagnation, oscillation, and infinite retry loop breaking | COMPLIANT |
| `codex-runtime-repair` | standalone | runtime-operator | Runtime repair, launcher wiring, dependency restoration | COMPLIANT |

---

## 2. Review, Anti-Bloat, Security & Verification

| Skill | Type | Target Roles | Core Capabilities | Budget Status |
| :--- | :--- | :--- | :--- | :--- |
| `oracle-review` | role-bundle / canonical | reviewer, oracle | Independent Stage 8 audit: absorbs `hallucination_auditor` (AgentHallu taxonomy), `implementation-review` (6 high-precision defect categories), and `minimalist-review` (Karpathy minimalism) | COMPLIANT |
| `security-audit` | standalone / canonical | whitehat, reviewer, auditor | Full & guidance audit: absorbs `security-review`, STRIDE threat modeling, and SecureCoder pre/post-fix verification | COMPLIANT |
| `scope-drift-control` | standalone | pm, oracle, reviewer | File and feature scope tracking against planned budgets | COMPLIANT |
| `auto-verification-harness` | standalone | oracle, tester | Autonomous verification harness scaffolding and plan checking | COMPLIANT |

---

## 3. Architecture, Planning & Orchestration

| Skill | Type | Target Roles | Core Capabilities | Budget Status |
| :--- | :--- | :--- | :--- | :--- |
| `senior-architect` | standalone | architect, sa | ADR authorship, reversibility scoring (1-5), C4 topology (Mermaid), NFR metrics, resiliency invariants | COMPLIANT |
| `routing-thresholds` | standalone | pm, oracle | Complexity tiering (Fast-Track, Standard, Epic, Wave) | COMPLIANT |
| `project-documentation` | standalone | pm, architect | PRD-to-delivery document chain (Epic specs, story breakdown) | COMPLIANT |
| `requirement-interviewer` | standalone | pm | Scope elicitation and ambiguity resolution | COMPLIANT |
| `spawn-governance` | standalone / canonical | pm, all subagents | Bounded subagent spawning and worktree file ownership; absorbs `delegate-task` | COMPLIANT |
| `worktree-isolation` | standalone | pm, all writers | Git worktree parallel execution with symlink caching | COMPLIANT |
| `unlazy` | standalone | pm, all builders | Enforces completion discipline, acceptance gates, Depth Tree decomposition | COMPLIANT |
| `archify` | standalone | architect, designer | Generates interactive HTML/SVG architecture, sequence, and workflow diagrams from system prompts or Mermaid inputs | COMPLIANT |

---

## 4. UI/UX, Frontend & Creative Engineering

| Skill | Type | Target Roles | Core Capabilities | Budget Status |
| :--- | :--- | :--- | :--- | :--- |
| `ui-ux-craft` | standalone / canonical | designer, dev-fe | Production frontend engineering: absorbs `frontend-design` (aesthetic direction & workflow) and `visual-engineer` (token pre-work, design intelligence); 5 Feels enforcement, OKLCH tokens, 60/120fps budgets, layout stability (CLS=0), motion physics | COMPLIANT |
| `ui-ux-audit` | standalone / canonical | reviewer, designer, oracle | Comprehensive UI/UX audit: absorbs `frontend-qc` (Finish Gate) and `design-review` (visual audit, violation tiers); 19 invariants, visual symmetry, breathability, motion sync | COMPLIANT |
| `animation-mastery` | standalone | designer, dev-fe | Spring physics, motion vocabulary, curve correctness, state transitions, Apple web design | COMPLIANT |
| `humanize-text` | standalone | writer, all agents | Eliminating AI buzzwords, natural cadence, prose de-roboting | COMPLIANT |

---

## 5. Testing, QA & Discovery

| Skill | Type | Target Roles | Core Capabilities | Budget Status |
| :--- | :--- | :--- | :--- | :--- |
| `e2e_testing` | standalone | tester, reviewer | Complete bug sweeps: functional, boundary, security, resilience | COMPLIANT |
| `regression-strategy` | standalone | pm, oracle, tester | Risk-based test selection, property-based testing (PBT) triggers, consumer contract verification | COMPLIANT |
| `codegraph-explorer` | standalone | explorers | CodeGraph-first exploration before broad grep scans | COMPLIANT |
| `axi-tools` | standalone | all agents | Token-efficient AXI CLI tools returning compact TOON output | COMPLIANT |
| `browseros-neo` | standalone | all agents | Dedicated logged-in agent browser via BrowserOS Neo MCP for live web reading, actions, and verification | COMPLIANT |
| `ground-truth-retrieval` | standalone | researcher, all agents | Fetch real-time external ground truth and documentation without hallucination | COMPLIANT |

---

## 6. Memory, Context & Token Economy

| Skill | Type | Target Roles | Core Capabilities | Budget Status |
| :--- | :--- | :--- | :--- | :--- |
| `adhd-mode` | standalone | all agents | Action-first output shaping with numbered steps, uncapped lists, and anchored state | COMPLIANT |
| `context-rot-prevention` | standalone | all agents, pm | Cognitive health telemetry, 3-strike read budget, mid-session ledger, Tier C pinning | COMPLIANT |
| `sot-context` | standalone / canonical | pm, all agents | Curated Source-of-Truth loading; absorbs `cognifold-memory` (semantic caching & folding), `graph-memory` (relations & traversal), and `mcp-knowledge` (one-shot `codex_knowledge` tools) | COMPLIANT |
| `document-sync` | standalone | doc-sync-worker | Syncing approved changes to documentation and Obsidian vault | COMPLIANT |
| `harness-deficiency-audit` | standalone | meta-evolution | Audit framework for diagnosing deficiencies, token bloat, loop bugs | COMPLIANT |

---

## Loading & Governance Rules

1. **Progressive Disclosure**: Load only the skills mandated by the task contract.
2. **Prefer Role Bundles**: For specialist agents, load the designated role bundle rather than disparate individual skills.
3. **1% Budget Invariant**: Combined active skill descriptions in prompts MUST remain $\le 1\%$ of context.
