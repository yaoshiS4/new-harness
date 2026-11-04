# Full protocol: routing-thresholds

Loaded on demand; see SKILL.md for triggers and core rules.

## 3-Tier Adaptive Routing & Delegation Protocol

| Execution Path | Complexity | Delegation Topology | Writer Invariant |
|---|---|---|---|
| **Path 1: Quick Route** | Atomic ($\le 3$ files, 1 domain) | Delegated Builder Subagent: Root Orchestrator (`pm`) frames inline Story Shard $\rightarrow$ spawns 1 Builder (`dev-fe` \| `dev-be` \| `debugger`). | **PM never writes code.** Builder has sole write lease on target files. |
| **Path 2: Normal Route** | Medium / Standard (4–10 files, 2 domains) | Disjoint Specialist Builders: Root Orchestrator (`pm`) frames `implementation_plan.md` + `task.md` with BMAD Story Shards $\rightarrow$ spawns disjoint Builders $\rightarrow$ Two-Stage Read-Only QC (7a `frontend-qc` + 7b `test-runner`) $\rightarrow$ Oracle. | **PM never writes code.** Builders strictly execute within leased files. QC/Oracle are read-only. |
| **Path 3: Long-Horizon Route** | Epic / Deep Arch (> 10 files, $\ge 3$ domains, `/goal`) | Deep Orchestration: Parallel 3-Explore $\rightarrow$ Architect Spec & ADR (`sa`) $\rightarrow$ PM Depth-Tree (`PLAN.md` + `GATES.md`) $\rightarrow$ Adversarial Plan Gate $\rightarrow$ Wave-Isolated Builders in Git Worktrees (`worktree-isolation`) $\rightarrow$ Context Checkpointing $\rightarrow$ 3-Round Zero-Bug Loop. | **PM never writes code.** Architect never writes feature code. Builders work in isolated worktrees. Max 2 write agents per wave. |

Hard limits:
- **Zero PM Code Mutation**: Root Orchestrator & PM (`subagent_type: "pm"`) NEVER directly mutates application source code (`apps/**`, `packages/**`, `src/**`, etc.) in any execution path.
- Max 2 write-capable agents active at once.
- Max 3 agents per wave.
- If a task would need > 3 agents, split it into sequential waves.
- Do not spawn for a task that lacks explicit output requirements, allowed files, required tests, and scope drift budget.


---
## Regression Thresholds

| Change Type | Required Validation |
|---|---|
| Docs/comment-only, no generated artifacts | Spell/format or targeted readback; no full regression unless docs drive runtime behavior. |
| Atomic code or config, <= 3 files, no shared contract | Focused tests for touched behavior plus the project fast structural gate when available. |
| Shared core logic, generation scripts, profile/tracker/config files, skills, workflow/rules, build/runtime config, or 4-10 files | Project full regression gate when available, plus focused tests for changed behavior. |
| Cross-package, architecture, migration, dependency, auth/security, data-loss risk, generated artifacts, or > 10 files | Assert-fresh before broad edits when available, full regression before completion, and reviewer/Oracle gate. |
| Self-healing runtime fix | Reproduction command before and after, affected smoke test, full runtime/project validation when available. |
| Self-evolving harness change | Harness syntax/readback check, relevant workflow smoke test, and KPI rollback criteria recorded. |

When a project exposes both `assert-fresh` and `run`, use `assert-fresh` before widening the edit surface and `run` before completion.

## Self-Healing Thresholds

Route to self-healing only when at least one condition is true:
- A runtime/tool/MCP/service command fails reproducibly twice with the same root symptom.
- A required regression or doctor gate is blocked by runtime configuration, missing wiring, or stale generated state.
- The user explicitly asks to repair the runtime, launcher, connector, MCP server, or local harness.

Do not route product bugs or feature requests to self-healing unless the failure is in the runtime/harness itself.

## Self-Evolving Thresholds

Route to self-evolving only when all prerequisites and at least one trigger are met.

Prerequisites:
- Evidence is validated by tests, Oracle/reviewer review, or explicit user confirmation.
- **Rolling-Trajectory Data Boundary (`rolling_trajectory`)**: Raw validated task traces must be clustered for near-duplicates first, then split into **70% Evolution Pool** (used for diagnosis & hypothesis formation) and **30% Validation Reserve** (strictly forbidden during diagnosis/design).
- **3-Axis Causal Attribution + Single-Hypothesis Rule**: Every diagnosed failure must be attributed to `Content` (domain/project knowledge), `Tool` (MCP/script capability), or `Schema` (rule/contract structure), locking exactly 1 causal hypothesis per shadow candidate (`vN-cK`).
- **Shadow Candidate Isolation (`vN-cK` vs. `active.json`)**: Changes are staged as shadow candidate `vN-cK` (`quick=2` or `full=8` round budget) and recorded via `codex_knowledge` (`knowledge_capture` / `memory_store`), never mutating live skills or `active.json` until validation passes on the 30% Validation Reserve with zero regressions.
- The proposed change is limited to skills, workflows, guardrails, prompts, or routing policy, and rollback criteria are known before editing.

Triggers:
- The same failure pattern appears in >= 3 validated tasks or traces.
- Two independent Oracle/reviewer findings identify the same harness gap.
- A tracked KPI worsens by >= 10% against the last accepted baseline.
- A user explicitly asks to improve the agent/runtime process after a validated failure.

Human approval is required before changing core orchestration, model policy, safety policy, or global runtime behavior.

## Deterministic Triage

Native Antigravity routing and `codex_knowledge` tools leverage deterministic heuristics for sub-millisecond categorical triage:
- **Topology & Complexity:** Classifies ambiguous user intent into `atomic`, `medium`, or `epic` classes based on file count, domains, and operational risk.
- **Contract Alignment:** Checks scope drift between original request and validated intent.
- **Diff Minimalism & Anti-Tampering:** Evaluates diff bloat and verifies test assertions were not weakened or deleted (Fix-The-Code-Not-The-Test invariant).

## Output

```yaml
routing_thresholds:
  execution_path: <path_1_quick|path_2_normal|path_3_long_horizon>
  complexity_class: <atomic|medium|epic>
  matched_thresholds:
    - <specific threshold>
  topology: <single_builder_delegation|disjoint_builders_sequential|parallel_worktree_spawn>
  regression_depth: <focused_plus_fast_gate|full_regression|assert_fresh_plus_full_regression>
  pm_code_mutation_allowed: false # ALWAYS false across all tiers
  self_healing_allowed: <true|false>
  self_evolving_allowed: <true|false>
  approval_required: <true|false>
```
