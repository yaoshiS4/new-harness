---
name: coordination
description: Multi-agent coordination, contract rules, lock protocols, and handoff specifications.
---

# Coordination Rules

## Contract Rules
- Use Markdown or YAML contracts only.
- No free form subagent chatter.
- Every handoff must name owner, files, risks, and next action.

## Lock Protocol
- Constitution Gate: project constitution must be generated and approved before any other work
- Cross-Artifact Consistency Gate verifies spec -> plan -> tasks chain before implementation
- Convergence Gate compares delivered codebase against spec before final review
- Scope Lock Gate freezes atomic tasks and validation targets
- Harness Activation Gate selects task-scoped skills, rules, workflows, and MCP tools
- Plan Review Gate requires Oracle independent critique and Oracle update of the Implementation Plan before implementation begins

## 3-Tier Adaptive Execution Pipeline
- **Adaptive Routing Across All Sessions**:
  - **Path 1: Quick Route (`workflows/fast-track.md`, `<= 3` files, 1 domain, zero schema/migration risk)**: `1. Intake & Inline Story Shard -> 2. Delegated Builder Fix (1 subagent) -> 3. Fast Verification Gate` (zero `implementation_plan.md` ceremony; PM never edits application code directly).
  - **Path 2: Normal Route (`workflows/standard-dev.md`, `4-10` files or 2 domains)**: Full 8-Stage Pipeline (`1. User Feedback -> 2. Enrichment -> 3. Clarification -> 4. PM Contract & Story Shards -> 5. Disjoint Specialist Builders -> 6. Surgical Implementation -> 7. Two-Stage QC -> 8. Independent Oracle Audit`) with `implementation_plan.md` and `task.md`.
  - **Path 3: Long-Horizon Route (`workflows/sol-sequential.md`, `> 10` files or `>= 3` domains)**: Deep Orchestration with Parallel 3-Explore, Architect Spec (`sa`), PM Depth-Tree (`unlazy`), Adversarial Plan Gate (`critical-planner`), Worktree Builders, Checkpointing, 3-Round Zero-Bug Loop, and Doc Sync.
- **System Audit (`workflows/system-audit.md`)**: Structured 10-section forensic, performance, and reliability audit.

## Task Breakdown & List Discipline
- Antigravity runtime does NOT auto-create `task.md`. For Path 2 and Path 3 tasks, the agent MUST explicitly create `<appDataDir>/brain/<conversation-id>/task.md` via `write_to_file` (`ArtifactMetadata: {"ArtifactType": "task", "UserFacing": true, "RequestFeedback": false, "Summary": "..."}`).
- Every Implementation Plan MUST be accompanied or immediately followed by this actionable, phased Task Checklist (`task.md`).
- Tasks must use markdown checkbox syntax (`- [ ]`, `- [/]`, `- [x]`), declare clear dependencies, parallel markers (`[P]`), and be updated continuously during execution.

## Memory Policy
- Record memory only after validation and approval
- Do not auto-learn from unreviewed changes
- Use semantic-cache-first retrieval before broad searches

## Model Policy (Gemini-Only Routing) & Subagent Dispatch
- Strictly bind all agents and subagents to Gemini models (`gemini-4-argon-*` and `gemini-3.8-flash-*`).
- **Native TypeName vs Role Dispatch Rule**: Antigravity's `invoke_subagent` natively supports exactly 3 built-in `TypeName` values: `research` (read-only tools), `self` (full write/audit/build tools), and `image-generator` (or custom types defined via `define_subagent`). Never pass specialist persona names as raw `TypeName` directly; pass them in the `Role` parameter:
  - **Tier A (`Model: "pro"` / `gemini-4-argon-high`)**: `TypeName: "self"` with `Role: "pm" | "sa" | "senior-architect" | "critical-planner" | "oracle-review" | "hallucination-auditor" | "whitehat" | "debugger"`.
  - **Tier B (`Model: "pro"` / `gemini-4-argon-medium` & `low`)**: `TypeName: "self"` with `Role: "dev-fe" | "dev-be" | "designer" | "visual-engineer" | "simplifier-reviewer" | "meta-evolution"`; or `TypeName: "image-generator"` (`gemini-4-argon-low`).
  - **Tier C (`Model: "flash"` / `gemini-3.8-flash-high`)**: `TypeName: "research"` with `Role: "backend-explorer" | "frontend-explorer" | "research-explorer" | "user-tester" | "devops" | "skillopt-optimizer" | "test-runner"`.
  - **Tier D (`Model: "flash"` / `"flash_lite"` / `gemini-3.8-flash-medium` & `low`)**: `TypeName: "research"` with `Role: "doc-sync-worker" | "librarian"` or telemetry/diff/status helpers.
- Load only the native role bundle for the current task.
- If a model tier is unavailable, fall back to the nearest supported Gemini model.
- Independent Oracle review uses `gemini-4-argon-high` (`--effort xhigh` in CLI or `Model: "pro"` in `invoke_subagent`).

## Oracle Review
- Oracle review is mandatory after each major phase
- In PM delegation workflows, Oracle independently critiques the Implementation Plan & Task Breakdown and hardens the plan via a dedicated `## Oracle Hardening & Directives` block (annotating risk mitigations, test criteria, and sign-off) without rewriting author sections
- In single-agent IDE sessions (where subagent spawning is unavailable), the agent MUST mechanically execute an internal Phase 2: Oracle Hardening Pass (loading `critique` & `hallucination-auditor`) and append `## Oracle Hardening, Directives & Verification Matrix` to `implementation_plan.md` BEFORE requesting user approval (`request_feedback: true`)
- Oracle mandates atomic synchronization into `task.md` prior to builder execution
- Final Review Gate checks tests, spec compliance, scope adherence, harness adherence, and hallucination audit
- Hallucination audit uses AgentHallu taxonomy via `hallucination-auditor` or independent review gate
- FabricatedReference or CommandInvention findings = automatic FAIL
- If the project exposes a native regression gate, use `project-regression assert-fresh` before broad edits and `project-regression run` before completion

## PM Gate
- `pm` classifies the request before implementation starts
- `pm` enriches vague requests and asks the user when ambiguity changes scope
- `pm` owns the task contract, validation target, scope drift budget, and final handoff

## SOL Pipeline (definitive — see also `workflows/sol-sequential.md`)
- Clarify Gate resolves ambiguities and emits the task contract
- 3-Explore Phase runs backend, frontend, and research exploration
- Scope Lock Gate freezes atomic tasks and validation targets
- Harness Activation Gate selects task-scoped skills, rules, workflows, and MCP tools
- Plan Formulation & Task Breakdown produces Implementation Plan and phased Task List
- Plan Review & Hardening Gate: Oracle independently critiques the plan, appends binding directives, and synchronizes tasks
- Cross-Artifact Consistency Gate: Verifies Spec $\leftrightarrow$ Plan $\leftrightarrow$ Tasks before code mutation
- Implementation Gate executes only the approved and Oracle-hardened plan
- Final Review Gate checks tests, spec compliance, scope adherence, harness adherence, and hallucination audit

## Loop Engineering
- All major processes are governed loops with bounded iteration, reflection, and early-stop
- Development: classify, enrich, read project SOT, inspect relevant files, patch, validate with targeted test runs (capped at max 2 re-verification attempts before reporting residual risk), summarize
- QC: independent review (including hallucination audit), then fix or ship
- Research: official and current sources first, no mutation
- Memory capture: only after validation and approval

## Self-Evolution
- Self-evolution follows the SkillOpt → AHE → AEvo chain
- Dreaming/Sleep consolidation runs at session end or token budget > 90%
- Use `workflows/dreaming-consolidation.md` for end-of-session consolidation
