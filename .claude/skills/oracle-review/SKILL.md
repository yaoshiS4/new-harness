---
name: oracle-review
description: Role bundle for Oracle review, drift checks, hallucination audit, and release gating.
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# Oracle Review (Stage 8 Independent Audit & Release Gate)

## Purpose
Independent, strictly read-only audit verifying truth, source backing, defect freedom, scope containment, and minimalism before release. Never write or mutate application code during review.

## 1. AgentHallu Audit Taxonomy (Zero Hallucination Gate)
Classify any inconsistencies before release. FabricatedReference or CommandInvention = automatic FAIL.
- **Fabricated Reference**: Referencing functions, classes, files, or packages that do not exist in the codebase.
- **State Divergence**: Claiming a test has passed or a service is running without actually executing it or checking fresh execution logs.
- **Scope Creep**: Implementing features or modifying files outside of the Scope Lock / Story Shard contract.
- **Command Invention**: Proposing shell commands that are invalid, uninstalled, or unsupported.

## 2. High-Precision Defect Categories (Confidence Floor >= 0.85)
Audit filtered diffs (`${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/clean-diff.sh`) against the 6 critical defect classes:
1. `LOGIC_CORRECTNESS`: Incomplete requirements, broken invariants, state corruption.
2. `NULL_SAFETY`: Unchecked null/nil pointers, undefined property dereferencing.
3. `CONCURRENCY`: Mutex deadlocks, race conditions, uncoordinated shared state.
4. `RESOURCE_LIFECYCLE`: Unclosed file/socket handles, connection leaks, timer leaks.
5. `BOUNDARY_ERROR`: Off-by-one indices, division by zero, unhandled empty collections.
6. `INJECTION_SECURITY`: Unparameterized queries, unsanitized sinks, path traversal.

*Position-Drift Verification*: Every cited defect MUST provide a 3-tuple `(file_path, line_number, exact_verbatim_snippet)` verified against live source.

## 3. Karpathy Minimalism & Diff Discipline
Enforce the smallest valid diff that satisfies the task contract:
- **Diff Ratio & File Budget**: Added lines <= 2x removed lines; file count strictly within shard allocation.
- **No Unnecessary Abstractions**: Zero speculative generalizations, zero "just in case" code, zero premature optimization.
- **No Duplication**: Extract shared utility only when logic appears in 3+ places; keep inline if in 1-2 places.
- **Surgical Changes**: Zero unrelated refactoring, zero gratuitous formatting/style drift mixed with functional changes.

## 4. Structured Output Format
```yaml
oracle_review:
  verdict: <APPROVE|REQUEST_CHANGES|REJECT>
  confidence: <0.85-1.00>
  hallucination_check:
    status: <PASS|FAIL>
    fabricated_refs: []
    state_divergence: []
    scope_creep: []
  defects:
    - category: <LOGIC_CORRECTNESS|NULL_SAFETY|CONCURRENCY|RESOURCE_LIFECYCLE|BOUNDARY_ERROR|INJECTION_SECURITY>
      severity: <BLOCKER|CRITICAL|MAJOR|MINOR>
      file: <path>
      line: <number>
      anchor_snippet: <verbatim code snippet>
      detail: <actionable defect explanation>
      fix: <concrete recommended patch>
  minimalism:
    score: <score>
    unnecessary_abstractions: []
    verdict: <PASS|FAIL>
  debt_introduced: <NONE|MINOR|MODERATE|MAJOR>
  residual_risk: <LOW|MEDIUM|HIGH>
```

---

## 5. Verification Before Completion Gate

Before certifying any implementation as complete or signing off:
1. **Capture Verification Baseline**: Verify prior test state, build status, and compiler/diagnostic errors.
2. **Execute Targeted Test Suite**: Run project test suites; verify zero regressions and complete coverage over changed code paths.
3. **Build & Static Analysis Check**:
   - TypeScript: `tsc --noEmit`
   - Rust: `cargo check`
   - Python: `python3 -m py_compile <files>` and unit tests
4. **Scope Contract Conformance**: Check that every acceptance criterion is satisfied and only `allowed_files` were mutated (`git status --short`).
5. **AOP Consistency & Minimalist Diff Check**: Ensure zero contradictions across claims, relations, and contracts, with clean surgical diffs free of bloat.

---

## 6. 6-Stage Lexicographic Deliverable Selection & Blinded Evaluation (Harness² Protocol)

Evaluates candidate deliverables strictly in lexicographic hierarchy: an earlier stage failure terminates evaluation immediately without considering subsequent stages (`1. Delivery -> 2. Conformance -> 3. Fidelity -> 4. Internal Consistency -> 5. Operational Fitness -> 6. Finish`).

```text
                      ╭──────────────────────────────╮
                      │ 1. Delivery: Non-empty files │
                      ╰──────────────────────────────╯
                                      │ [Pass]
                                      ▼
    ╭──────────────────────────────╮    ╭──────────────────────────────╮
    │ DISQUALIFIED: Missing Del... │    │ 2. Conformance: Scope lease  │
    ╰──────────────────────────────╯    ╰──────────────────────────────╯
                    │                                   │
                    ▼                                   ▼
    ╭──────────────────────────────╮    ╭──────────────────────────────╮
    │ DISQUALIFIED: Scope Lease... │    │ 3. Fidelity: Zero halluc...  │
    ╰──────────────────────────────╯    ╰──────────────────────────────╯
                    │                                   │
                    ▼                                   ▼
    ╭──────────────────────────────╮    ╭──────────────────────────────╮
    │ DISQUALIFIED: Fidelity Ga... │    │ 4. Internal Consistency      │
    ╰──────────────────────────────╯    ╰──────────────────────────────╯
                    │                                   │
                    ▼                                   ▼
    ╭──────────────────────────────╮    ╭──────────────────────────────╮
    │ DISQUALIFIED: Inconsisten... │    │ 5. Operational Fitness       │
    ╰──────────────────────────────╯    ╰──────────────────────────────╯
                    │                                   │
                    ▼                                   ▼
    ╭──────────────────────────────╮    ╭──────────────────────────────╮
    │ DISQUALIFIED: Operational... │    │ 6. Finish: Karpathy minimal  │
    ╰──────────────────────────────╯    ╰──────────────────────────────╯
                    │                                   │
                    ▼                                   ▼
                      ╭──────────────────────────────╮
                      │ DISQUALIFIED: Polish / Sl... │
                      ╰──────────────────────────────╯
```

### 6-Stage Lexicographic Evaluation Criteria

1. **Stage 1 (Delivery)**:
   - Verifies the deliverable exists on disk, is non-empty, and target files have been produced.
   - Zero-byte files or missing deliverables fail immediately.
2. **Stage 2 (Conformance)**:
   - Verifies strict containment within the Story Shard lease (`allowed_files`).
   - Zero mutations to unleased files. Zero tampering with core system hooks or immutable invariants.
3. **Stage 3 (Fidelity)**:
   - Verifies all functional requirements and explicit acceptance criteria are satisfied.
   - Evaluates against the AgentHallu taxonomy: zero fabricated references, zero state divergence, zero invented commands.
4. **Stage 4 (Internal Consistency)**:
   - Verifies architectural and semantic coherence across modified files.
   - Zero broken imports, zero type signature mismatches, zero conflicting duplicate definitions or contradictory invariants.
5. **Stage 5 (Operational Fitness)**:
   - Verifies that all code compiles (`py_compile`, `tsc --noEmit`, `cargo check`) and targeted tests pass with zero regressions.
   - Zero resource leaks, zero unhandled boundary conditions, zero concurrency deadlocks.
6. **Stage 6 (Finish)**:
   - Enforces Karpathy minimalism: added lines $\le 2\times$ removed lines, zero speculative generalizations.
   - UI Anti-Slop verification: zero nested cards (L-01), zero card soup (L-13), zero badge proliferation (D-09).
   - Documentation integrity preserved; zero leftover debug print statements or task tracking tags in code comments.

### Blinded Candidate Selection Protocol (Multi-Candidate Evaluation)

When evaluating competing candidate rollouts (e.g., Path 3 parallel worktrees or Level-1 intra-task candidates $\mathcal{H}^{(t)}$):
- **Anonymized Candidate Masking**: Strip builder identity, commit history, and session identifiers. Label candidates with cryptographically shuffled tags (`Candidate A`, `Candidate B`, etc.).
- **Lexicographic Rank-Ordering**: Rank each candidate through Stages 1–6 in order. A candidate that passes through Stage $k$ strictly outranks any candidate that failed at Stage $< k$.
- **Harmony (`arXiv:2610.15150`) CP-2 3-Axis Pareto Non-Dominated Gate**: Every candidate mutation must be Pareto non-dominated across all 3 axes (`func_score >= base`, `sec_score >= 1.0`, `token_score >= base`) with strict improvement on at least one axis; any security guardrail degradation (`sec_score < 1.0`) is unconditionally rejected.
- **Tie-Breaking via Behavioral Delta ($\Delta_{\text{behav}}$)**: If multiple candidates reach Stage 6, calculate the behavioral delta against the baseline reference:
  $$\Delta_{\text{behav}} = (\text{err}_{\text{base}} - \text{err}_{\text{cand}}) + 2(\text{jev}_{\text{base}} - \text{jev}_{\text{cand}}) + (\text{strikes}_{\text{base}} - \text{strikes}_{\text{cand}})$$
  Enforce the **`KEEP_BASE` default**: Retain baseline unless the candidate demonstrates $\Delta_{\text{behav}} > 0$.

### Anti-Leak Firewall

- **Harness Isolation**: The verification harness and test assertions operate out-of-process and are never exposed to candidate builders during generation (`Fix-The-Code-Not-The-Test`).
- **Read-Only Auditor Contract**: The Oracle review agent (`subagent_type: "oracle-review"`) possesses strictly read-only capabilities. Code mutations during audit are mechanically blocked by `pre_tool_use.py`.
- **Verdict Finality & EGRP Requirement**: Any blocking audit finding MUST cite verifiable evidence formatted as `[Evidence: <path:line> | <ast_symbol_or_cmd_output>]` along with a 3-tuple `(file_path, line_number, anchor_snippet)`. Speculative audit claims or rebuttals without concrete disk or command output backing are automatically downgraded to `NON-BLOCKING NIT` and cannot force a Builder revert.

### VeriHarness Consensus Challenger & Oracle Custody Audit

- **Consensus Challenger (`arXiv:2610.00972`)**: Challenge points where implementation and agent-authored tests unanimously agree; verify assertions against original user prompt rather than implementation behavior. Identify shared specification blind spots or colluding assertions where tests validate the builder's chosen implementation rather than the canonical specification.
- **Oracle Custody Lease (`arXiv:2610.28667`)**: Existing test assertions and expected literals are immutable by default; intentional breaking API changes require `Oracle-Custody-Lease: UPDATE_ASSERTIONS` in the Story Shard. Without an explicit custody lease, test edits that weaken, loosen, or remove existing assertions are rejected (`Fix-The-Code-Not-The-Test`).

---

## 7. Elephant-Goldfish Stateless Isolation Protocol (`google/elephant-goldfish-model`)

> *"Design with an elephant. Review with a goldfish."*

### Core Mechanism
- **Elephant (`pm` / `sa` / Root Author)**: Holds deep project history, cross-turn context, and trade-off discussions while drafting `implementation_plan.md` or Story Shards.
- **Goldfish (`oracle-review` / Reviewer Subagent)**: Evaluates specs, plans, and diffs with a strict **Stateless Mindset** — zero conversation history, zero inherited unstated assumptions, and strictly read-only tools. The Goldfish reads only the written specification/diff and its explicitly referenced files as a fresh team member.
- **Fail-Closed Readability Rule**: If a required referenced file or symbol cannot be read or verified on disk, return `INCOMPLETE_REVIEW` immediately rather than guessing a verdict or assuming unstated context.

### The 4 Specialized Goldfish Lenses
1. **`design_critic` (Hostile Design & Economics Critic)**:
   - Audits quantitative scale and resource bounds: peak QPS, storage footprint, DB query load ($N+1$ queries, unindexed scans), LLM token budgets, latency budgets, and Single Points of Failure (SPOFs).
2. **`zoom_out` (Skeptical YAGNI Architect)**:
   - Enforces radical simplicity and anti-overengineering: flags speculative abstractions, missed codebase reuse (`codegraph:symbol_lookup`), and architectural dead-ends.
3. **`implementation_readiness` (Pragmatic Tech Lead)**:
   - Verifies that zero design decisions are left to the Builder (`dev-fe` / `dev-be`): exact file paths, function signatures, error envelopes, and deterministic verification commands must be fully specified.
4. **`comprehension` & `synthesizer` (Fresh-Reader Clarity & Trade-Off Matrix)**:
   - Flags ambiguous prose or hidden chat assumptions invisible to a zero-context reader, and reconciles multi-Goldfish critiques into a prioritized, deduplicated decision and trade-off matrix.

---

## 8. Multi-Lens Parallel Fan-Out & Git Tree-Fingerprint Convergence

- **4-Lens Parallel Fan-Out (`--lenses bug-hunter,security,bird-eye,code-quality`)**:
  - `bug-hunter`: Logic errors, null/undefined dereferences, boundary off-by-one bugs, race conditions, and unhandled failure paths.
  - `security`: Injection vectors, symlink/path traversal escapes, secret leaks, auth bypass, and untrusted external content handling.
  - `bird-eye`: End-to-end architectural coherence, cross-module contracts, Story Shard scope containment, and regression risk.
  - `code-quality`: Karpathy minimalism, dead/duplicate code removal, zero speculative abstractions, and clean maintainability.
- **Git Tree-Fingerprint Convergence (`--fingerprint-state <state.json>`, max 3 rounds)**:
  - Computes SHA-256 over `git rev-parse HEAD` + `git status --porcelain` + `git diff HEAD` via `ensure-verification-gates.py`.
  - Halts review loops immediately when the tree fingerprint is unchanged between rounds (`tree_fingerprint_unchanged`) or when `max_rounds=3` is reached.



