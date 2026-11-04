---
name: harness-deficiency-audit
description: Audit framework for diagnosing deficiencies, token bloat, loop bugs, and architectural flaws in agent harnesses.
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# Harness & Codebase Deficiency Audit Framework

Use this skill whenever asked to review, audit, health-check, or harden either:
1. **Agent Harness & Runtime Environment** (Antigravity/Codex settings, rules, hooks, token economy, MCP tooling).
2. **Target Application Codebase** (any repository: architecture, infinite loops, race conditions, memory leaks, error handling, test integrity, dependencies).

---

## Audit Execution Modes

Identify the target scope from the user prompt:
- **Mode A: Harness & Environment Audit** - Audits IDE configs, lifecycle hooks, rule coherence, token economy, and MCP servers.
- **Mode B: Codebase & Architecture Audit** - Audits application source code, logic bugs, deadlocks, resource leaks, tests, and security flaws.
- **Mode C: Unified Dual Audit** - Audits both the agent harness and the target repository end-to-end.

---

## Mode A: Agent Harness & Runtime Protocol

Execute across these 6 vectors when auditing the harness:

### 1. Rule & Contract Conflict Analysis
- **Precedence Hierarchy**: Verify workspace `AGENTS.md` strictly supersedes global defaults.
- **Pipeline vs Oracle Invariant**: Verify that all tasks execute the Universal 8-Stage Pipeline without bypasses, and Oracle review enforces minimal payload transfer.
- **Contradiction Sweep**: Ensure no rule mandates an action that another rule bans.

### 2. Loop & Deadlock Vulnerability Audit
- **Anti-Poll Ban**: Verify zero `while ... ps`, `tail -f`, or bash `sleep` loops.
- **Three-Strike File Read Gate**: Check that `Read` is mechanically bounded to 3 reads per file without edits before requiring targeted slicing.
- **Async Deadlock Guard**: Ensure background tasks have single-task watchdog conditions and no tight status-query loops.
- **Hook Recursion**: Verify hooks cannot invoke tools that recursively trigger the same hook.

### 3. Token Economy & Prompt Cache Preservation
- **System Prefix Immutability**: Verify Tier A (`system_prefix.md` and tool schemas) is 100% byte-identical across turns.
- **Dynamic Content Channeling**: Route dynamic context (memory seeds, warnings, plan alerts) strictly via Tier C ephemeral messages (`additionalContext`).
- **Static Skill Footprint**: Audit `skills.json` to ensure niche design, marketing, or academic skills are excluded from eager prompt injection (<3,000 tokens overhead).
- **Tool Output Compression**: Verify clean test suites and command outputs are truncated/summarized, while errors retain full tracebacks.

### 4. Hook & Gate Integrity Check
- **Fail-Safe Containment**: Every hook handler must wrap execution in top-level `try/except Exception` blocks, log cleanly to stderr, and exit 0 to prevent freezing IDE tool dispatch.
- **Input/Output Contract Conformance**:
  - `PreToolUse`: Output must be `{"permissionDecision": "allow" | "deny" | "ask"}`.
  - `PostToolUse`: Output must be `{}`.
  - `PreInvocation`: Output must be `{"additionalContext": [...]}`.
- **Regex Robustness**: Ensure command interceptors strip quoted arguments before evaluating syntax to avoid false positive blocks.

### 5. IDE & Runtime Platform Drift
- **Deep Watcher & Search Excludes**: Verify compiler/linter/env caches (`.pixi`, `.pytest_cache`, `.ruff_cache`, `.turbo`, `.next`, `.gradle`, `.cargo/registry`) are excluded from file watchers.
- **LSP Scoping**: Ensure `"python.analysis.diagnosticMode": "openFilesOnly"` is set to stop full-workspace virtualenv thrashing.
- **Native Extension Binaries**: Check that platform-specific binaries (e.g. `pet` for Python Environments) exist and have execute permissions (`chmod +x`).
- **Syntax Validation**: Ensure `settings.json` strictly adheres to RFC 8259 JSON (no trailing commas).

### 6. Anti-Hallucination & Evidence Hardening
- **Assertion Immutability ("Fix Code, Never Weaken Tests")**: Strictly enforce that failing tests are solved by fixing implementation code, never by softening assertions.
- **Strict Evidence Citation**: Ensure all completion and pass claims cite the exact executed command line, return code `0`, and a stdout snippet.
- **Symbol-First Exploration**: Follow global mechanical read bounds: read files `<= 200` lines whole first; for files `> 400` lines, require AST/symbol lookup (`mcp__codegraph__symbol_lookup()`, `mcp__codegraph__summarize_path()`) before reading targeted slices `<= 250` lines.

---

## Mode B: Codebase & Architecture Protocol

Execute across these 6 vectors when auditing any target repository:

### 1. Architectural & Contract Integrity
- **Circular Dependencies**: Scan for import cycles (e.g., A imports B imports A) that cause initialization deadlocks or `undefined` runtime references.
- **Boundary Leaks**: Check that domain boundaries are respected (e.g., UI components not directly querying raw databases; business logic decoupled from transport/protocols).
- **Dead Code & Orphan Modules**: Detect unused exports, unreferenced utility files, and orphaned functions using CodeGraph (`mcp__codegraph__impact_analysis()` / `mcp__codegraph__summarize_path()`).

### 2. Logic Loops, Race Conditions & Deadlocks
- **Unbounded Loops**: Inspect all `while` and recursive functions for deterministic termination invariants, timeout bounds, and exit state mutations.
- **Async Concurrency & Race Conditions**: Check for unawaited async calls, floating Promises, shared mutable state accessed without locks, or missing cleanup in teardowns.
- **Resource Deadlocks**: Identify lock acquisition ordering issues in multithreaded code or transaction deadlocks in database operations.

### 3. Error Handling & Fault Resilience
- **Silent Exception Swallowing**: Detect empty `catch {}` or `except: pass` blocks that swallow root causes and mask critical failures.
- **Trust Boundary Sanitization**: Verify that all user inputs, API payloads, and query parameters undergo strict schema validation before processing.
- **Crash Isolation**: Ensure background worker errors or unhandled rejections do not take down the main application process.

### 4. Resource Leaks & Performance Bottlenecks
- **Resource Lifecycle**: Check that file descriptors, sockets, streams, database pool connections, and timers (`setInterval`) are guaranteed to close in `finally` / `cleanup` blocks.
- **Memory Retention**: Inspect long-lived caches, global event listeners, and detached DOM/widget references for unbounded growth.
- **Algorithmic Complexity**: Flag O(N^2) nested iterations over unbounded collections, N+1 query patterns, and redundant JSON serialization in hot loops.

### 5. Test Suite & Assertion Integrity
- **Assertion Softening ("Fix Code, Never Weaken Tests")**: Audit test suites for weakened assertions, skipped tests (`.skip`, `xit`), or mock objects returning constant truthy values.
- **Test Determinism**: Verify that tests do not rely on non-deterministic sleeps (`sleep(500)`), arbitrary network calls, or system clock state.
- **Edge Case Coverage**: Check critical business branches for zero-input, null/empty, boundary, and error-recovery test cases.

### 6. Security, Secrets & Dependency Health
- **Secrets in Source**: Sweep source code and git history for hardcoded tokens, API keys, private certificates, or internal URLs.
- **Vulnerability Audit**: Check project dependencies for known CVEs (`npm audit`, `pip-audit`, `cargo audit`).
- **Unpinned Floating Dependencies**: Ensure lockfiles (`package-lock.json`, `poetry.lock`, `Cargo.lock`) are committed and dependency versions are pinned.

---

## Automated Verification Suite

Run the applicable command suite during audits:

### Harness Verification Commands
- Validate configs: `python3 -m json.tool <path_to_json> > /dev/null`
- Lifecycle hooks regression: `python3 -m unittest discover -s ~/.claude/hooks/tests -p "test_*.py"`
- Mechanical harness tree validator: `python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/validate-claude-tree.py`
- Recursive PPC engine self-test: `python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/recursive-ppc-engine.py --self-test`
- Experience reflector self-test: `python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/reflect-experience.py --self-test`
- Native Python locator binary: `~/.antigravity-ide/extensions/ms-python.python-*/python-env-tools/bin/pet --version`

### Codebase Verification Commands (Targeted)
- TypeScript/JavaScript syntax: `node -c <target_file>` or targeted linting
- Circular dependency scan: `npx madge --circular <entry_path>`
- Python syntax & types: `python3 -m py_compile <target_file>` / `ruff check <target_file>`
- Targeted test run: `PRE_SHIP=1 npm test -- <targeted_test_file>` / `pytest <path_to_test>`

---

## 7. Skill Optimization & Evolution Guardrails (SkillOpt Protocol)

When refining or evolving skill instruction documents or task overlays:
1. **Freeze Parent & Split Traces**: Freeze the parent skill version and partition historical traces into a 70% Evolution Pool (for failure diagnosis) and a 30% Validation Reserve (strictly held-out and sealed).
2. **3-Axis Causal Attribution**: Attribute every deficiency to exactly one axis: `Content` (missing domain knowledge), `Tool` (MCP/CLI gap), or `Schema` (contract structure).
3. **Orthogonal Proposer Separation (`INV` vs `DOM`)**:
   - `meta-invariant-editor` (`INV`): Strictly leased to execution mechanics (`tool-quirks.md`, loop/guardrail config, subagent routing). Forbidden from editing domain skills or application code.
   - `meta-domain-editor` (`DOM`): Strictly leased to practitioner artifacts (`.claude/harness/SKILL.md`, `.claude/harness/scripts/*.py`). Forbidden from editing hooks or global rules.
4. **Deterministic Contrastive Behavioral Probe & `KEEP_BASE` Default**:
   - Compare reference rollout telemetry $e^{(t-1)}$ against candidate probe telemetry $e_{\text{cand}}$ across 4 verifier-free metrics: `(tool_error_count, read_budget_strikes, jev_loop_warnings, deliverable_non_empty)`.
   - Compute $\Delta_{\text{behav}} = (\text{err}_{t-1} - \text{err}_{\text{cand}}) + 2(\text{jev}_{t-1} - \text{jev}_{\text{cand}}) + (\text{strikes}_{t-1} - \text{strikes}_{\text{cand}}) + \delta_{\text{deliv}}$.
   - Enforce `KEEP_BASE` default: reverts to $\mathcal{H}^{(t-1)}$ whenever $\Delta_{\text{behav}} \le 0$ or any candidate script fails `py_compile`.
5. **4-Way Causal Attribution & `NO_ENTRY` Anti-Hallucination Gate**:
   - Assign each candidate an explicit causal verdict: `helped`, `hurt`, `no_observed_effect`, or `confounded` (when multiple unisolated edits occurred without behavioral contrast).
   - If verdict $\in \{\text{hurt}, \text{no\_observed\_effect}, \text{confounded}\}$ or `confidence == "low"`, trigger `NO_ENTRY`: write zero bytes to `SkillBank` / `registry.sqlite`.
6. **Bounded Patching**: Enforce textual learning-rate budgets (max 3 operations or <= 20% changed lines per round).
7. **Held-Out Validation & Zero Regressions**: Score candidates on the sealed 30% reserve. Promote only when `candidate_score > parent_score`, regressions == 0, and Oracle review passes.
8. **No Blind Mutations**: Never edit live skill definitions in place without staging shadow candidates first.
