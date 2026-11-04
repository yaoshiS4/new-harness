---
name: routing-thresholds
description: Classifies task complexity, subagent topology, regression depth, and self-healing execution workflows.
triggers:
  - "complexity threshold"
  - "delegation threshold"
  - "spawn threshold"
  - "regression threshold"
  - "self-healing threshold"
  - "self-improvement threshold"
  - "self-evolving threshold"
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# Routing Thresholds

Use this skill during PM intake, Scope Lock, regression planning, self-healing intake, and self-evolving intake.

## 3-Tier Adaptive Routing & Complexity Classes

Classify by the highest matched threshold:

| Path | Class | Threshold | Workflow & Delegation |
|---|---|---|---|
| **Path 1: Quick Route** | Atomic | 1 clear concern; touches $\le 3$ files; 1 domain or package; no schema, dependency, migration, auth, payment, data-loss, or architecture change; clear intent. | Inline Story Shard in chat (zero `implementation_plan.md` ceremony) $\rightarrow$ 1 Builder subagent (`dev-fe` \| `dev-be` \| `debugger`) $\rightarrow$ Fast Verification Gate. **PM never writes code.** |
| **Path 2: Normal Route** | Medium / Standard | 4–10 files, or 2 domains/packages, standard features or tactical refactors, bounded blast radius. | 8-Stage Pipeline $\rightarrow$ PM contract (`implementation_plan.md` + `task.md`) $\rightarrow$ BMAD Story Shards $\rightarrow$ Disjoint Builder subagents (`dev-fe` / `dev-be`) $\rightarrow$ Two-Stage QC (7a static `frontend-qc` + 7b dynamic `test-runner`) $\rightarrow$ Oracle Audit. **PM never writes code.** |
| **Path 3: Long-Horizon Route** | Epic / Deep Arch | > 10 files, or $\ge 3$ domains/packages, new subsystem, architectural migration, multi-phase delivery, or `/goal`. | Parallel 3-Explore $\rightarrow$ Architect Spec & ADR (`sa`) $\rightarrow$ PM Depth-Tree (`PLAN.md` + `GATES.md` via `unlazy`) $\rightarrow$ Adversarial Plan Gate (`critical-planner` + `verify-oracle.sh --plan` scaffolded via `ensure-verification-gates.py`) $\rightarrow$ Wave-Isolated Builders in Git Worktrees (`worktree-isolation`) $\rightarrow$ Context Checkpoints $\rightarrow$ 3-Round Zero-Bug Loop (`test-3-round-loop.sh` scaffolded via `ensure-verification-gates.py`) $\rightarrow$ Doc Sync. **PM never writes code.** |

If uncertainty is high and the scope may cross a threshold, classify one level higher until exploration proves otherwise.

### Agentless 3-Step Localization Fast-Path (Path 1 <= 3 files)
On Path 1 tasks, bypass redundant Explorer subagent spawning:
1. **Direct Coordinate Discovery**: In Stage 1/2, use `codegraph` (`symbol_lookup`, `summarize_path`) or bounded `rg` directly to locate exact `path:line` coordinates without spawning Explorer subagents.
2. **Targeted Builder Delegation**: Ground the inline Story Shard with these exact coordinates and pass directly into 1 Builder subagent (`dev-fe` | `dev-be` | `debugger`).
3. **Fast Verification Gate**: Run targeted unit tests and compile checks (`run-compiled-qc.py`, `pytest`, `tsc`).

## Hard Role Invariant (Zero Toe-Stepping)
- Root Orchestrator & PM (`subagent_type: "pm"`) is strictly limited to intake, SOT grounding, clarification, complexity classification, and story shard / contract authoring.
- **PM NEVER writes or edits application source code** (`apps/**`, `packages/**`, `src/**`, `*.ts`, `*.tsx`, `*.py`, `*.kt`, etc.) in any tier. All code modifications are strictly delegated to dedicated Builder subagents (`dev-fe`, `dev-be`, `debugger`, `meta-evolution`).

## Full Protocol
Load `references/protocol.md` before executing beyond the core rules above.
