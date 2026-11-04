---
name: core-rules
description: Antigravity core operational lifecycle, classification gates, intake protocols, and context discipline.
---

# Core Rules

## 3-Tier Adaptive Routing Protocol & Strict Role Isolation (BMAD + CrewAI + LangGraph)

### Hard Role Invariant (Zero Toe-Stepping)
- **Root Orchestrator & `pm` (`Role: "pm"`)**: Strictly limited to request ingestion, SOT grounding, clarification (`ask_question`), complexity routing (`routing-thresholds`), Story Shard / `implementation_plan.md` / `task.md` authoring, and subagent orchestration. **NEVER** mutates application source code (`apps/**`, `packages/**`, `src/**`, `*.ts`, `*.tsx`, `*.py`, `*.kt`, etc.).
- **Explorers (`frontend-explorer`, `backend-explorer`, `research-explorer`)**: Strictly read-only (`TypeName: "research"`, `Model: "flash"`). Return file coordinates, line numbers, and telemetry; never write plans or code.
- **Architects (`sa`, `senior-architect`, `critical-planner`)**: Own system design, ADRs, and adversarial plan review (`Model: "pro"`). Never write application feature code.
- **Builders (`dev-fe`, `dev-be`, `debugger`, `designer`, `meta-evolution`)**: Exclusively execute Stage 6 code modifications (`TypeName: "self"`, `Model: "pro"`) within their leased Story Shard files (`allowed_files`). Never redefine requirements or touch unleased files.
- **QC & Auditors (`frontend-qc`, `test-runner`, `oracle-review`, `hallucination-auditor`, `implementation-review`)**: Strictly read-only inspectors/runners. Never self-edit application code during audit; route any `Fail: <path:line>` back to a Builder subagent.

### 3-Tier Adaptive Execution Paths
- **Path 1: Quick Route (`Atomic / Quick Flow` — `<= 3` files, 1 domain, zero schema/auth/migration risk, clear intent)**:
  1. *Intake & Inline Story Shard*: Ground SOT, emit inline Story Shard in chat (target files + acceptance criteria + test command; zero `implementation_plan.md` ceremony).
  2. *Delegated Builder Fix*: Spawn 1 Builder subagent (`TypeName: "self"`, `Role: "dev-fe" | "dev-be" | "debugger"`, `Model: "pro"`).
  3. *Fast Verification Gate*: Run targeted unit test + `tsc --noEmit` + UI anti-slop check (if UI touched).
- **Path 2: Normal Route (`Standard / Tactical` — `4–10` files or 2 domains, standard features/refactors)**:
  Execute the 8-Stage Pipeline: `1. Intake → 2. Enrichment (research/flash) → 3. Clarification → 4. PM Contract & Story Shards (implementation_plan.md + task.md) → 5. Disjoint Specialist Builders (dev-fe / dev-be) → 6. Surgical Implementation → 7. Two-Stage QC (7a Static frontend-qc + 7b Dynamic test-runner) → 8. Independent Oracle Audit (oracle-review + verify-oracle.sh)`.
- **Path 3: Long-Horizon Route (`Epic / Deep Architecture` — `> 10` files, `>= 3` domains, new subsystems/migrations, or `/goal`)**:
  Execute Deep Orchestration: `1. Parallel 3-Explore → 2. Architect Spec & ADR (sa) → 3. PM Depth-Tree & Story Shards (PLAN.md + GATES.md via unlazy) → 4. Adversarial Plan Gate (critical-planner + verify-oracle.sh --plan) → 5. Wave-Isolated Builders in Git Worktrees (worktree-isolation) → 6. Context Checkpointing (handoff_checkpoint at 60% budget) → 7. 3-Round Zero-Bug Loop (test-3-round-loop.sh + verify-oracle.sh) → 8. Doc Sync (doc-sync-worker)`.

- **Session Lifecycle Budget**: When a session reaches 8 user turns without epic completion, run `workflows/token-check.md`, record a checkpoint in local SOT (break-resume contract), and offer the user a fresh session. This trigger is reviewed by transcript turn-count, not runtime telemetry.

## Context Discipline & Exploration
- Read curated context and local SOT first.
- Prefer selected files, task lists, and structured summaries over repo-wide scans.
- When MCP servers are active in `~/.gemini/config/mcp_config.json`, use them for indexed exploration before broad grep/read; otherwise use targeted file and ripgrep inspection.
- Keep raw command output out of the active prompt whenever possible (apply compact summaries).

## Model Routing (Gemini-Only Matrix)
- Strictly use Gemini models across all sessions, CLI commands, and subagents (`gemini-4-argon-high`, `gemini-4-argon-medium`, `gemini-4-argon-low`, `gemini-3.8-flash-high`, `gemini-3.8-flash-medium`, `gemini-3.8-flash-low`).
- **Subagent TypeName vs Role Persona Contract**: Antigravity's native `invoke_subagent` registers exactly 3 built-in `TypeName` values: `research` (read-only exploration tools), `self` (full write/command tools, inheriting parent agent), and `image-generator` (or custom types defined via `define_subagent`). Specialist personas are mapped via the `Role` parameter:
  - Use `TypeName: "research"` with `Role: "<persona>"` for read-only exploration (`backend-explorer`, `frontend-explorer`, `research-explorer`, `user-tester`, `devops`, `skillopt-optimizer`, `doc-sync-worker`, `librarian`).
  - Use `TypeName: "self"` with `Role: "<persona>"` for write/command/audit workflows (`pm`, `sa` / `senior-architect`, `oracle-review`, `hallucination-auditor`, `dev-fe`, `dev-be`, `designer`, `visual-engineer`, `simplifier-reviewer`, `debugger`, `whitehat`, `meta-evolution`).
- **Tier A — Deep Reasoning & Governance (`Model: "pro"` | CLI `gemini-4-argon-high`)**: `TypeName: "self"` with `Role: "pm" | "sa" | "senior-architect" | "critical-planner" | "oracle-review" | "hallucination-auditor" | "whitehat" | "debugger"`, Stage 3 Clarification, Stage 4 PM Contract, Stage 6 Complex Fix (Builder `Role: "dev-fe" | "dev-be" | "debugger"` only; PM never writes code), and Stage 8 Independent Audit (`--effort xhigh`).
- **Tier B — Production Coding & UI Craft (`Model: "pro"` | CLI `gemini-4-argon-medium` / `low`)**: `TypeName: "self"` with `Role: "dev-fe" | "dev-be" | "designer" | "visual-engineer" | "simplifier-reviewer" | "meta-evolution"` (or `TypeName: "image-generator"` with `gemini-4-argon-low`), Stage 1 Intake, Stage 6 Standard Fix (`Role: "dev-fe" | "dev-be" | "debugger"`), and Stage 7 UI Anti-Slop QC.
- **Tier C — High-Speed Exploration & Test Runners (`Model: "flash"` | CLI `gemini-3.8-flash-high`)**: `TypeName: "research"` with `Role: "researcher" | "backend-explorer" | "frontend-explorer" | "research-explorer" | "user-tester" | "devops" | "skillopt-optimizer"`, Stage 2 Enrichment, and Stage 7 Test Execution (`Role: "test-runner"`).
- **Tier D — Docs Sync & Lightweight Telemetry (`Model: "flash"` / `"flash_lite"` | CLI `gemini-3.8-flash-medium` / `low`)**: `TypeName: "research"` with `Role: "doc-sync-worker" | "librarian"`, diff/status/telemetry helpers (`gemini-3.8-flash-low` / `flash_lite`).
- Do not load every skill or bundle at once (progressive disclosure).

## Delegation & Subagents
- Delegate only bounded, non-overlapping work.
- Give each subagent explicit ownership and scope.
- Keep subagent returns summary-only.
- Use Markdown or YAML contracts only.

## Validation & Review
- **Targeted Test Execution**: During active development, execute only the specific test file(s) for the patch (e.g. `npm test -- path/to/target.test.ts`). Reserve full test suite runs for pre-ship delivery gate.
- **Fast-Track Discovery Cap (≤ 10 Tool Steps)**: Exploration before drafting an implementation plan is capped at 10 tool steps. Ground hypotheses quickly using project SOT docs (`docs/SOT.md`, `README.md`) rather than aimless full-repo grepping.
- Run task-specific validation commands and regression tests.
- Verify before claiming completion.
- Report what was checked, what passed, and what remains risky.
- Oracle review is required after planning, implementation, validation, and release. Oracle review includes hallucination audit for all medium+ tasks. FabricatedReference or CommandInvention findings = automatic FAIL.
- **High-Precision Defect Taxonomy (adapted from Alibaba OCR)**: PR reviews and implementation audits evaluate: (1) Logic & Functional Correctness, (2) Security & Privacy, (3) Compliance vs `implementation_plan.md`. Report the complete, uncapped list of actionable findings (never truncate to top 5). Reported defects must map to concrete high-severity categories:
  1. `LOGIC_CORRECTNESS`: Incomplete requirements, broken invariants, state corruption, functional regressions.
  2. `NULL_SAFETY`: Unchecked null/nil pointers, undefined property dereferencing, missing optional chaining.
  3. `CONCURRENCY`: Mutex deadlocks, race conditions, goroutine/worker thread leaks, uncoordinated shared state.
  4. `RESOURCE_LIFECYCLE`: Unclosed file/socket handles, connection leaks, uncancelled timeouts or event listeners.
  5. `BOUNDARY_ERROR`: Off-by-one indices, division by zero, unhandled empty collections.
  6. `INJECTION_SECURITY`: Unparameterized queries, unsanitized HTML/DOM sinks, SSRF vectors.
  - **Confidence Floor ($\ge 0.85$)**: Review findings must achieve verifiable confidence based on test evidence, LSP/type diagnostics, or deterministic code proof. Speculative, unverified, or subjective stylistic nits below 0.85 are suppressed.

## Pre-Generation Minimalism Ladder (adapted from ponytail)
Before writing code, stop at the first rung that solves the problem:
1. **Does this need to exist?** -> No: skip it (YAGNI).
2. **Already in this codebase?** -> Reuse existing functions, components, or helpers; do not rewrite.
3. **Standard library does it?** -> Use standard library or platform API.
4. **Native platform feature?** -> Use browser/OS/framework built-in primitives.
5. **Installed dependency?** -> Use already-installed packages; enforce safety with `scan_dependencies` before importing or requesting any new packages.
6. **One line?** -> Keep it to a clean single expression or standard one-liner.
7. **Only then: write the minimum code that works.** Trust-boundary validation, security, and accessibility are never skipped.

- **4-Angle Anti-Bloat Diff Review (fcakyon, motivated by Karpathy critique)**: Before committing or completing any implementation, review the code against four angles:
  1. **Reuse**: Check if existing project helpers, types, or utilities can be reused before creating new abstractions.
  2. **Simplification**: Eliminate speculative generalization, unnecessary indirection, and "just in case" code.
  3. **Efficiency**: Ensure surgical execution paths with zero redundant passes or dead allocations.
  4. **Altitude**: Keep abstractions at the right layer; do not leak business logic into low-level drivers or vice-versa.

- **4-Pass Leaf Discipline (Anti-Laziness Invariant from Unlazy)**: For non-trivial subtasks and feature leaves, never stop at the initial MVP:
  1. **Pass 1 (Complete Deliverable)**: Implement the complete deliverable without placeholders, stubs, or deferred remainder.
  2. **Pass 2 (Domain Expert Refactor)**: Re-read as a domain expert; replace cheap/naive implementations with robust production-grade patterns.
  3. **Pass 3 (Defect & Edge Case Hunt)**: Hunt integration defects, concurrency issues, edge-case boundary errors, and regression vectors; fix what you find.
  4. **Pass 4 (Zero-Defect Polish)**: Apply low-cost polish, clean formatting, and verify clean test passes until an audit pass discovers zero issues.
## Anti-Hallucination Invariants (AgentHallu Defense)
- **Assertion Immutability ("Fix Code, Never Weaken Tests")**: In bug fix and refactoring workflows, modifying test assertions is strictly prohibited unless explicitly directed by the user with `ALLOW_TEST_EDIT=1`. If a test fails, fix the implementation code to satisfy the test contract. Never delete, weaken, or soften assertions to fake a passing test suite.
- **Strict Evidence Citation**: Never claim that a test suite, build, or verification step passed without quoting the exact executed terminal command line, exit code `0`, and a 1–2 line stdout snippet. Unsubstantiated completion assertions are treated as critical hallucination failures.
- **Symbol-First AST Discovery**: For files exceeding 100 lines, use `codegraph:summarize_path` or `codegraph:symbol_lookup` to locate relevant functions, classes, or types before reading. Restrict subsequent reads to targeted line slices (`StartLine`/`EndLine`) instead of full file dumps.
- **Interface Grounding**: NEVER guess component props, function signatures, or enum variants. Always inspect the TypeScript interface (via `codegraph`, or line-range `view_file`) before writing consumer code.
- **Environment Grounding**: Verify CLI tool availability with `command -v <tool>` or inspect `package.json` scripts before executing non-standard shell commands.
- **Artifact Path Anchor**: Always reference artifacts in `<appDataDir>/brain/<conversation-id>/`, never in the workspace root.

## UI & Content Guardrails (Anti-Slop Laws & Post-Coding Fix Gate)
- **Strict Guardrail Invariants**: For all UI, layout, or frontend tasks, strictly enforce `guidelines/ui-apex-invariants.md` and `guidelines/anti-slop-taxonomy.md`. Zero tolerance for nested cards (L-01), carditis / card soup (L-13), tag-left / header-right splits (L-14), icon-as-bullet fatigue (T-12), pill / badge proliferation (D-09), two-line CTA wrapping (L-15), careless ellipsis truncation / mid-word clipping (L-16), state geometry jitter (M-07), re-drawn OS/browser chrome (I-05), and over-expressing / noun-echo prefixes (W-07).
- **Mandatory Post-Coding Anti-Slop Fix Pass**: Immediately after generating or modifying UI components, execute an explicit anti-slop review and remediation pass (applying `skills/ui-ux-audit`). Any detected nested containers, repetitive bullet icons, unnecessary badge pills, truncated mid-word stubs, or layout reflows MUST be actively refactored and flattened before executing tests or claiming completion.
- **Eliminate Redundant Section Subtitles**: NEVER generate generic, echoey subtitle/subtext underneath section titles. Section titles must be self-sufficient and authoritative with Eyebrow + Title alone. Subtitles that rephrase or pad section titles are strictly banned as AI slop.
- **Clean Compound String Wrapping & Divider Break**: When long compound text contains dividers (such as `·`, `*`, `/`, `-`, or parentheses `(...)`), calculate available viewport width. NEVER permit flexbox/browser auto-wrapping to cut clumsily in the middle of words or phrases of the second clause. If text length exceeds single-line budget, deliberately break at the divider: move the entire second part after the divider to a clean, dedicated new line (`\n`) or multi-line structured layout.

## Autonomous Skill Triggers
- **Ground-Truth Retrieval**: Auto-trigger `skills/ground-truth-retrieval` when an external library API, version discrepancy, or remote package error is encountered.
- **ADHD Output Mode**: DEFAULT GLOBAL MODE. All outputs follow `skills/adhd-mode` (Action-first, The 10 Golden Rules, anchored state, full uncapped lists, zero conversational filler) unless the user explicitly requests "normal mode".
- **Loop Circuit Breaker**: On turn 3 of identical failure signatures, enforce the 3-Turn Debug Spiral Hard Stop before touching code again.

## Safety
- Ask before adding dependencies, deleting files, changing architecture, migrations, or pushing.
- Do not auto-capture durable memory without approval.
- Do not run multiple write-capable agents on the same branch at once.
- Keep scope drift under the approved threshold.

